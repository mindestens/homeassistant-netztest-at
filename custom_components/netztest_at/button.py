"""Button to start an RTR measurement now."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import RtrConfigEntry
from .const import DOMAIN
from .entity import RtrEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: RtrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([RtrRunButton(entry.runtime_data, "run_test", "button")])


class RtrRunButton(RtrEntity, ButtonEntity):
    """Runs one test in the background (takes ~30-60 s)."""

    _attr_icon = "mdi:speedometer"

    async def async_press(self) -> None:
        self.coordinator.config_entry.async_create_background_task(
            self.hass, self.coordinator.async_run_test(), f"{DOMAIN}_button_test"
        )
