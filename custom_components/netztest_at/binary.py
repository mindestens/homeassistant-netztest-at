"""Download and verify the RTR client binary from this integration's GitHub release."""

from __future__ import annotations

import hashlib
import logging
import os
import platform

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import BIN_DIR, BIN_PATH, BINARY_NAMES, CHECKSUM_FILE, RELEASE_URL, VERSION

_LOGGER = logging.getLogger(__name__)


class BinaryError(Exception):
    """The RTR client could not be provided."""


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_binary(data: bytes) -> None:
    os.makedirs(BIN_DIR, exist_ok=True)
    tmp = BIN_PATH + ".part"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.chmod(tmp, 0o755)
    os.replace(tmp, BIN_PATH)
    with open(BIN_PATH + ".sha256", "w", encoding="ascii") as fh:
        fh.write(f"{VERSION} {hashlib.sha256(data).hexdigest()}")


def _installed_ok() -> bool:
    """Binary present, executable and unchanged since it was verified."""
    if not os.access(BIN_PATH, os.X_OK):
        return False
    marker = BIN_PATH + ".sha256"
    if not os.path.isfile(marker):
        return False
    with open(marker, encoding="ascii") as fh:
        # A new integration version may ship a new client build: re-download then.
        return fh.read().strip() == f"{VERSION} {_sha256(BIN_PATH)}"


async def async_ensure_binary(hass: HomeAssistant) -> None:
    """Make sure the matching client binary is installed; download and verify it if not."""
    if await hass.async_add_executor_job(_installed_ok):
        return

    arch = platform.machine().lower()
    name = BINARY_NAMES.get(arch)
    if name is None:
        raise BinaryError(f"unsupported CPU architecture: {arch} (supported: x86_64, aarch64)")

    session = async_get_clientsession(hass)
    try:
        async with session.get(RELEASE_URL.format(version=VERSION, name=CHECKSUM_FILE), timeout=30) as resp:
            resp.raise_for_status()
            sums = await resp.text()
        expected = next((line.split()[0] for line in sums.splitlines() if line.strip().endswith(name)), None)
        if not expected:
            raise BinaryError(f"no checksum for {name} in {CHECKSUM_FILE}")
        async with session.get(RELEASE_URL.format(version=VERSION, name=name), timeout=120) as resp:
            resp.raise_for_status()
            data = await resp.read()
    except BinaryError:
        raise
    except Exception as err:  # noqa: BLE001 - network errors of any kind
        raise BinaryError(f"download of {name} failed: {err}") from err

    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise BinaryError(f"checksum mismatch for {name}: expected {expected}, got {actual}")

    await hass.async_add_executor_job(_write_binary, data)
    _LOGGER.info("Installed RTR client %s (%s, sha256 %s)", name, VERSION, actual)
