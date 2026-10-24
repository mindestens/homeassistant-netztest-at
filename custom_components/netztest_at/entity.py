"""Base entity for Netztest AT."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RtrCoordinator


class RtrEntity(CoordinatorEntity[RtrCoordinator]):
    """Common device and naming for all Netztest AT entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RtrCoordinator, key: str, platform: str) -> None:
        super().__init__(coordinator)
        # Fixed English entity IDs, independent of the UI language.
        self.entity_id = f"{platform}.{DOMAIN}_{key}"
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Netztest AT",
            manufacturer="Netztest AT (unofficial)",
            model="RTR-Netztest client (Open-RMBT)",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://www.netztest.at",
        )
