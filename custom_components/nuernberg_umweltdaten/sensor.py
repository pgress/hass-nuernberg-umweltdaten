"""Sensor platform for the Nürnberg Umweltdaten integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_DATE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_STATION_CODE,
    CONF_STATION_NAME,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .coordinator import NuernbergDataUpdateCoordinator
from .measures import MEASURES

_LOGGER = logging.getLogger(__name__)

ATTR_LAST_MEASURED = "last_measured"
ATTR_STATION_CODE = "station_code"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one sensor per field that the chosen station actually provides."""
    data: dict[str, Any] = hass.data[DOMAIN][entry.entry_id]
    coordinator: NuernbergDataUpdateCoordinator = data["coordinator"]
    fields: list[str] = data["fields"]

    async_add_entities(
        NuernbergSensor(coordinator, entry, field) for field in fields
    )


class NuernbergSensor(CoordinatorEntity[NuernbergDataUpdateCoordinator], SensorEntity):
    """A single measured value of a Nürnberg Umweltdaten station."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NuernbergDataUpdateCoordinator,
        entry: ConfigEntry,
        field: str,
    ) -> None:
        super().__init__(coordinator)
        self._field = field
        self._entry = entry

        desc = MEASURES[field]
        station_code = entry.data[CONF_STATION_CODE]

        self._attr_unique_id = f"{station_code}_{field}"
        self._attr_translation_key = desc.translation_key
        self._attr_native_unit_of_measurement = desc.unit
        self._attr_device_class = desc.device_class
        self._attr_state_class = desc.state_class
        self._attr_icon = desc.icon

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data[CONF_STATION_CODE])},
            name=self._entry.data.get(CONF_STATION_NAME),
            manufacturer=MANUFACTURER,
            model=MODEL,
            suggested_area="Outdoor",
        )

    @property
    def native_value(self) -> float | None:
        snapshot: dict[str, Any] = self.coordinator.data or {}
        value = snapshot.get(self._field)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        snapshot: dict[str, Any] = self.coordinator.data or {}
        return {
            ATTR_LAST_MEASURED: snapshot.get("date_entry"),
            ATTR_STATION_CODE: self._entry.data[CONF_STATION_CODE],
        }
