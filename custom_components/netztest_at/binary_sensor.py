"""Shows whether an RTR measurement is running right now."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import RtrConfigEntry
from .entity import RtrEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: RtrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([
        RtrRunningSensor(entry.runtime_data, "running", "binary_sensor"),
        RtrForeignServerSensor(entry.runtime_data, "server_abroad", "binary_sensor"),
    ])


class RtrRunningSensor(RtrEntity, BinarySensorEntity):
    """On while the client is measuring."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.running


class RtrForeignServerSensor(RtrEntity, BinarySensorEntity):
    """On if the last test ran against a server outside Austria (or one not recognised as Austrian)."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        if "server_in_austria" not in data:
            return None
        return not data["server_in_austria"]

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        return {"server": (self.coordinator.data or {}).get("server")}
