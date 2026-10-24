"""Netztest AT: scheduled internet speed tests with the official RTR-Netztest client (unofficial integration)."""

from __future__ import annotations

import asyncio
import logging
import random

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store

from .binary import BinaryError, async_ensure_binary
from .const import (
    CONF_ACCEPT_TERMS,
    CONF_RANDOM_DELAY,
    CONF_SCHEDULE_ENABLED,
    CONF_START_TIMES,
    DEFAULT_RANDOM_DELAY,
    DEFAULT_SCHEDULE_ENABLED,
    DOMAIN,
    MAX_TESTS_PER_DAY,
    MIN_GAP_MINUTES,
    SERVICE_RUN_TEST,
    STORAGE_VERSION,
)
from .coordinator import RtrCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BUTTON, Platform.BINARY_SENSOR]

type RtrConfigEntry = ConfigEntry[RtrCoordinator]


def option(entry: ConfigEntry, key: str, default):
    """Options override the values from the initial setup."""
    return entry.options.get(key, entry.data.get(key, default))


def parse_times(text: str) -> list[tuple[int, int]]:
    """Parse "03:00, 19:00" into [(3, 0), (19, 0)]; raises ValueError on bad input."""
    times: list[tuple[int, int]] = []
    for part in text.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        hour, minute = (int(x) for x in part.split(":")[:2])
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError(part)
        if (hour, minute) not in times:
            times.append((hour, minute))
    if not times:
        raise ValueError("no time given")
    if len(times) > MAX_TESTS_PER_DAY:
        raise ValueError("too many times")
    mins = sorted(h * 60 + m for h, m in times)
    if len(mins) > 1:
        gaps = [b - a for a, b in zip(mins, mins[1:])] + [mins[0] + 1440 - mins[-1]]
        if min(gaps) < MIN_GAP_MINUTES:
            raise ValueError("times too close")
    return sorted(times)


async def async_setup_entry(hass: HomeAssistant, entry: RtrConfigEntry) -> bool:
    """Set up Netztest AT from a config entry."""
    if not option(entry, CONF_ACCEPT_TERMS, False):
        # RTR requires explicit consent before the test may be used; the client reports it as accepted.
        raise ConfigEntryError("RTR-Netztest terms and privacy policy not accepted - accept them in the integration options")
    try:
        await async_ensure_binary(hass)
    except BinaryError as err:
        raise ConfigEntryNotReady(f"RTR client not available: {err}") from err

    coordinator = RtrCoordinator(hass, entry)
    await coordinator.async_load()
    entry.runtime_data = coordinator

    text = option(entry, CONF_START_TIMES, "")
    if option(entry, CONF_SCHEDULE_ENABLED, DEFAULT_SCHEDULE_ENABLED) and text:
        times = parse_times(text)
        max_delay = int(option(entry, CONF_RANDOM_DELAY, DEFAULT_RANDOM_DELAY) or 0)

        async def _delayed_test() -> None:
            # Optional random delay spreads the load on RTR's servers across installations.
            if max_delay:
                await asyncio.sleep(random.uniform(0, max_delay * 60))
            await coordinator.async_run_test()

        @callback
        def _scheduled(_now) -> None:
            entry.async_create_background_task(hass, _delayed_test(), f"{DOMAIN}_scheduled_test")

        for hour, minute in times:
            entry.async_on_unload(async_track_time_change(hass, _scheduled, hour=hour, minute=minute, second=0))
        _LOGGER.debug("Tests scheduled daily at %s", ", ".join(f"{h:02d}:{m:02d}" for h, m in times))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))

    if not hass.services.has_service(DOMAIN, SERVICE_RUN_TEST):

        async def _run_test(call: ServiceCall) -> None:
            for loaded in hass.config_entries.async_loaded_entries(DOMAIN):
                await loaded.runtime_data.async_run_test()

        hass.services.async_register(DOMAIN, SERVICE_RUN_TEST, _run_test)

    return True


async def _async_reload(hass: HomeAssistant, entry: RtrConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: RtrConfigEntry) -> None:
    """Delete the stored last result when the integration is removed."""
    await Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}").async_remove()


async def async_unload_entry(hass: HomeAssistant, entry: RtrConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded and not hass.config_entries.async_loaded_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_RUN_TEST)
    return unloaded
