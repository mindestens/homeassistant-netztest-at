"""Run the official RTR-Netztest C client (rmbt-client) and keep the last result."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import statistics
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    AUSTRIA_SERVER_PATTERN,
    BIN_PATH,
    CONTROL_SERVER,
    DOMAIN,
    ISSUE_FOREIGN_SERVER,
    OTHER_SPEEDTEST_PROCESSES,
    OTHER_SPEEDTEST_WAIT_MAX,
    OPENTEST_API,
    RESULT_URL,
    STORAGE_VERSION,
    TEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class RtrTestError(Exception):
    """Raised when a measurement fails."""


def parse_client_output(stdout: str) -> dict[str, Any]:
    """Parse the -v JSON lines of rmbt-client into a result dict."""
    pings: list[float] = []
    final: dict[str, Any] | None = None
    submit: dict[str, Any] | None = None
    error: str | None = None
    server_host: str | None = None

    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("Server:"):
            server_host = line.split(":", 1)[1].strip().split(" ")[0]
            continue
        if not line.startswith("{"):
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        kind = msg.get("type")
        if kind == "PING_RESULT" and isinstance(msg.get("pingServer"), (int, float)):
            pings.append(float(msg["pingServer"]))
        elif kind == "FINAL_RESULT":
            final = msg
        elif kind == "SUBMIT_RESULT":
            submit = msg
        elif kind == "STATE_CHANGE" and msg.get("state") == "ERROR":
            error = f"{msg.get('phase')}: {msg.get('error')}"

    if final is None:
        raise RtrTestError(error or "no FINAL_RESULT in client output")

    jitter = None
    if len(pings) >= 2:
        jitter = round(statistics.fmean(abs(b - a) for a, b in zip(pings, pings[1:])), 3)

    return {
        "download": round(float(final["down"]), 2),
        "upload": round(float(final["up"]), 2),
        "ping": round(float(final["pingMedian"]), 2),
        "ping_min": round(min(pings), 2) if pings else None,
        "ping_max": round(max(pings), 2) if pings else None,
        "jitter": jitter,
        "ping_count": final.get("pingCount"),
        "download_threads": final.get("downThreads"),
        "upload_threads": final.get("upThreads"),
        "test_uuid": final.get("testUuid"),
        "open_test_uuid": final.get("openTestUuid"),
        "submitted": bool(submit and submit.get("success")),
        "server_host": server_host,
    }


def server_in_austria(*names: str | None) -> bool:
    """True if any of the server name / host matches RTR's Austrian naming."""
    return any(n and re.search(AUSTRIA_SERVER_PATTERN, n, re.IGNORECASE) for n in names)


class RtrCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Holds the last measurement; tests run only on schedule or on demand."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=None)
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self._lock = asyncio.Lock()
        self.running = False
        self.last_error: str | None = None
        self.home_dir = hass.config.path(".storage", DOMAIN)

    async def async_load(self) -> None:
        """Restore the last result after a restart."""
        stored = await self._store.async_load()
        if stored:
            self.last_error = stored.pop("_last_error", None)
            self.async_set_updated_data(stored)

    async def _other_speedtest_running(self) -> bool:
        """True while a known speed-test program runs on this system (needs pgrep; missing pgrep = no check)."""
        for name in OTHER_SPEEDTEST_PROCESSES:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "pgrep", "-x", name,
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
                )
            except OSError:
                return False
            if await proc.wait() == 0:
                return True
        return False

    async def _fetch_opentest(self, open_uuid: str) -> dict[str, Any]:
        """Provider and server name come from RTR's open data API (may lag a few seconds)."""
        session = async_get_clientsession(self.hass)
        for attempt in range(4):
            await asyncio.sleep(5 + attempt * 5)
            try:
                async with session.get(OPENTEST_API.format(uuid=open_uuid), timeout=20) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        if data.get("server_name") or data.get("provider_name"):
                            return data
            except Exception as err:  # noqa: BLE001 - open data is optional
                _LOGGER.debug("Open data fetch failed (attempt %d): %s", attempt + 1, err)
        return {}

    def _update_foreign_issue(self, result: dict[str, Any]) -> None:
        """Show a repair issue while the last test ran against a server outside Austria."""
        if result.get("server_in_austria"):
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_FOREIGN_SERVER)
            return
        _LOGGER.warning("RTR assigned a test server outside Austria (or unknown): %s", result.get("server"))
        ir.async_create_issue(
            self.hass, DOMAIN, ISSUE_FOREIGN_SERVER,
            is_fixable=False, severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_FOREIGN_SERVER,
            translation_placeholders={"server": str(result.get("server") or result.get("server_host") or "?")},
        )

    async def async_run_test(self) -> None:
        """Run one measurement; keeps the previous result if it fails."""
        if self._lock.locked():
            _LOGGER.info("RTR test already running, request ignored")
            return
        async with self._lock:
            self.running = True
            self.async_update_listeners()
            try:
                waited = 0
                while waited < OTHER_SPEEDTEST_WAIT_MAX and await self._other_speedtest_running():
                    await asyncio.sleep(5)
                    waited += 5
                if waited:
                    _LOGGER.debug("Waited %d s for another running speed test", waited)

                await self.hass.async_add_executor_job(os.makedirs, self.home_dir, 0o700, True)
                proc = await asyncio.create_subprocess_exec(
                    BIN_PATH, "-h", CONTROL_SERVER, "-v",
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                    env={"HOME": self.home_dir, "PATH": "/usr/bin:/bin"},
                )
                try:
                    out, err = await asyncio.wait_for(proc.communicate(), TEST_TIMEOUT)
                except TimeoutError as exc:
                    proc.kill()
                    await proc.wait()
                    raise RtrTestError(f"client did not finish within {TEST_TIMEOUT} s") from exc

                stdout = out.decode(errors="replace")
                try:
                    result = parse_client_output(stdout)
                except RtrTestError as exc:
                    tail = err.decode(errors="replace").strip()[-300:]
                    raise RtrTestError(f"{exc} (exit {proc.returncode}) {tail}".strip()) from exc

                result["last_test"] = dt_util.utcnow().isoformat()
                open_uuid = result.get("open_test_uuid")
                if open_uuid:
                    result["result_url"] = RESULT_URL.format(uuid=open_uuid)
                    opendata = await self._fetch_opentest(open_uuid)
                    result["server"] = opendata.get("server_name") or result.get("server_host")
                    result["provider"] = opendata.get("provider_name")
                    result["implausible"] = opendata.get("implausible")
                else:
                    result["server"] = result.get("server_host")
                result["server_in_austria"] = server_in_austria(result.get("server"), result.get("server_host"))
                self._update_foreign_issue(result)

                self.last_error = None
                await self._store.async_save(result)
                self.async_set_updated_data(result)
                _LOGGER.info(
                    "RTR test done: %.1f/%.1f Mbit/s, ping %.1f ms, server %s",
                    result["download"], result["upload"], result["ping"], result.get("server"),
                )
            except (RtrTestError, OSError) as exc:
                self.last_error = str(exc)
                _LOGGER.error("RTR test failed: %s", exc)
                if self.data:
                    await self._store.async_save({**self.data, "_last_error": self.last_error})
            finally:
                self.running = False
                self.async_update_listeners()
