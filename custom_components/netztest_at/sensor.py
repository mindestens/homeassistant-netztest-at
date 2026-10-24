"""Sensors for Netztest AT: values of the last RTR-Netztest measurement."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfDataRate, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import RtrConfigEntry, option
from .const import CONF_PLAN_DOWNLOAD, CONF_PLAN_UPLOAD
from .coordinator import RtrCoordinator
from .entity import RtrEntity


@dataclass(frozen=True, kw_only=True)
class RtrSensorDescription(SensorEntityDescription):
    """Describes how a sensor value is derived from the last result."""

    value: Callable[[dict[str, Any], RtrCoordinator], Any]


def _compliance(field: str, conf: str) -> Callable[[dict[str, Any], RtrCoordinator], Any]:
    def calc(data: dict[str, Any], coord: RtrCoordinator) -> float | None:
        plan = float(option(coord.config_entry, conf, None) or 0)
        if data.get(field) is None or plan <= 0:
            return None
        return round(data[field] / plan * 100, 1)

    return calc


def _rate(key: str) -> RtrSensorDescription:
    return RtrSensorDescription(
        key=key,
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value=lambda d, _c, k=key: d.get(k),
    )


def _ms(key: str) -> RtrSensorDescription:
    return RtrSensorDescription(
        key=key,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value=lambda d, _c, k=key: d.get(k),
    )


SENSORS: tuple[RtrSensorDescription, ...] = (
    _rate("download"),
    _rate("upload"),
    _ms("ping"),
    _ms("ping_min"),
    _ms("ping_max"),
    _ms("jitter"),
    RtrSensorDescription(
        key="download_plan_compliance",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value=_compliance("download", CONF_PLAN_DOWNLOAD),
    ),
    RtrSensorDescription(
        key="upload_plan_compliance",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value=_compliance("upload", CONF_PLAN_UPLOAD),
    ),
    RtrSensorDescription(key="server", value=lambda d, _c: d.get("server")),
    RtrSensorDescription(key="provider", value=lambda d, _c: d.get("provider")),
    RtrSensorDescription(
        key="result_url", entity_category=EntityCategory.DIAGNOSTIC, value=lambda d, _c: d.get("result_url")
    ),
    RtrSensorDescription(
        key="last_test",
        device_class=SensorDeviceClass.TIMESTAMP,
        value=lambda d, _c: dt_util.parse_datetime(d["last_test"]) if d.get("last_test") else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: RtrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    # Compliance sensors only exist when the contract value is set.
    skip = {
        key for key, conf in (("download_plan_compliance", CONF_PLAN_DOWNLOAD), ("upload_plan_compliance", CONF_PLAN_UPLOAD))
        if not option(entry, conf, None)
    }
    async_add_entities(RtrSensor(coordinator, desc) for desc in SENSORS if desc.key not in skip)


class RtrSensor(RtrEntity, SensorEntity):
    """One value of the last RTR measurement."""

    entity_description: RtrSensorDescription

    def __init__(self, coordinator: RtrCoordinator, description: RtrSensorDescription) -> None:
        super().__init__(coordinator, description.key, "sensor")
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        return self.entity_description.value(self.coordinator.data, self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key != "last_test":
            return None
        data = self.coordinator.data or {}
        return {
            "test_uuid": data.get("test_uuid"),
            "open_test_uuid": data.get("open_test_uuid"),
            "submitted_to_rtr": data.get("submitted"),
            "implausible": data.get("implausible"),
            "ping_count": data.get("ping_count"),
            "download_threads": data.get("download_threads"),
            "upload_threads": data.get("upload_threads"),
            "last_error": self.coordinator.last_error,
        }
