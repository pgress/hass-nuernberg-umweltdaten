"""Measure descriptors for the Nürnberg Umweltdaten integration.

Every field that can ever appear in a station snapshot is described here with its
unit, device class, state class and icon. At setup time only the fields that
actually carry a value for the chosen station become entities - fields that are
``null`` are skipped, so no "unknown" sensors are created.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass


def _dc(name: str) -> Optional[SensorDeviceClass]:
    """Resolve a device class by name, tolerant of older HA versions."""
    return getattr(SensorDeviceClass, name, None)


def _sc(name: str) -> Optional[SensorStateClass]:
    """Resolve a state class by name, tolerant of older HA versions."""
    return getattr(SensorStateClass, name, None)


@dataclass(frozen=True)
class MeasureDescriptor:
    """Static description of a single measurement."""

    key: str
    translation_key: str
    unit: Optional[str]
    device_class: Optional[SensorDeviceClass]
    state_class: Optional[SensorStateClass]
    icon: str


# Order matters only cosmetically: air -> weather -> water.
MEASURES: dict[str, MeasureDescriptor] = {
    # --- Außenluft ---------------------------------------------------------
    "nitrogen_monoxide": MeasureDescriptor(
        "nitrogen_monoxide", "nitrogen_monoxide", "µg/m³",
        _dc("NITROGEN_MONOXIDE"), _sc("MEASUREMENT"), "mdi:molecule",
    ),
    "nitrogen_oxides": MeasureDescriptor(
        "nitrogen_oxides", "nitrogen_oxides", "µg/m³",
        None, _sc("MEASUREMENT"), "mdi:molecule",
    ),
    "nitrogen_dioxide": MeasureDescriptor(
        "nitrogen_dioxide", "nitrogen_dioxide", "µg/m³",
        _dc("NITROGEN_DIOXIDE"), _sc("MEASUREMENT"), "mdi:molecule",
    ),
    "sulfur_dioxide": MeasureDescriptor(
        "sulfur_dioxide", "sulfur_dioxide", "µg/m³",
        _dc("SULPHUR_DIOXIDE"), _sc("MEASUREMENT"), "mdi:molecule",
    ),
    "ozone": MeasureDescriptor(
        "ozone", "ozone", "µg/m³",
        _dc("OZONE"), _sc("MEASUREMENT"), "mdi:air-filter",
    ),
    "ozone_8h": MeasureDescriptor(
        "ozone_8h", "ozone_8h", "µg/m³",
        _dc("OZONE"), _sc("MEASUREMENT"), "mdi:air-filter",
    ),
    "carbon_monoxide": MeasureDescriptor(
        "carbon_monoxide", "carbon_monoxide", "mg/m³",
        _dc("CARBON_MONOXIDE"), _sc("MEASUREMENT"), "mdi:molecule-co",
    ),
    "benzene": MeasureDescriptor(
        "benzene", "benzene", "µg/m³",
        None, _sc("MEASUREMENT"), "mdi:flask-outline",
    ),
    "toluene": MeasureDescriptor(
        "toluene", "toluene", "µg/m³",
        None, _sc("MEASUREMENT"), "mdi:flask-outline",
    ),
    "methane": MeasureDescriptor(
        "methane", "methane", "µg/m³",
        None, _sc("MEASUREMENT"), "mdi:molecule",
    ),
    "thc": MeasureDescriptor(
        "thc", "thc", "µg/m³",
        None, _sc("MEASUREMENT"), "mdi:molecule",
    ),
    "non_methane_hydrocarbon": MeasureDescriptor(
        "non_methane_hydrocarbon", "non_methane_hydrocarbon", "µg/m³",
        None, _sc("MEASUREMENT"), "mdi:molecule",
    ),
    "particulate_matter_pm10": MeasureDescriptor(
        "particulate_matter_pm10", "particulate_matter_pm10", "µg/m³",
        _dc("PM10"), _sc("MEASUREMENT"), "mdi:smog",
    ),
    "particulate_matter_pm2_5": MeasureDescriptor(
        "particulate_matter_pm2_5", "particulate_matter_pm2_5", "µg/m³",
        _dc("PM25"), _sc("MEASUREMENT"), "mdi:smog",
    ),
    "particulate_matter_pm10_raw": MeasureDescriptor(
        "particulate_matter_pm10_raw", "particulate_matter_pm10_raw", "µg/m³",
        _dc("PM10"), _sc("MEASUREMENT"), "mdi:smog",
    ),
    "particulate_matter_pm2_5_raw": MeasureDescriptor(
        "particulate_matter_pm2_5_raw", "particulate_matter_pm2_5_raw", "µg/m³",
        _dc("PM25"), _sc("MEASUREMENT"), "mdi:smog",
    ),
    # --- Wetterdaten -------------------------------------------------------
    "air_temperature": MeasureDescriptor(
        "air_temperature", "air_temperature", "°C",
        _dc("TEMPERATURE"), _sc("MEASUREMENT"), "mdi:thermometer",
    ),
    "air_humidity": MeasureDescriptor(
        "air_humidity", "air_humidity", "%",
        _dc("HUMIDITY"), _sc("MEASUREMENT"), "mdi:water-percent",
    ),
    "air_pressure": MeasureDescriptor(
        "air_pressure", "air_pressure", "hPa",
        _dc("PRESSURE"), _sc("MEASUREMENT"), "mdi:gauge",
    ),
    "wind_speed": MeasureDescriptor(
        "wind_speed", "wind_speed", "m/s",
        _dc("WIND_SPEED"), _sc("MEASUREMENT"), "mdi:weather-windy",
    ),
    "wind_speed_peak": MeasureDescriptor(
        "wind_speed_peak", "wind_speed_peak", "m/s",
        _dc("WIND_SPEED"), _sc("MEASUREMENT"), "mdi:weather-windy",
    ),
    "wind_direction": MeasureDescriptor(
        "wind_direction", "wind_direction", "°",
        None, _sc("MEASUREMENT"), "mdi:compass",
    ),
    "global_radiation": MeasureDescriptor(
        "global_radiation", "global_radiation", "W/m²",
        None, _sc("MEASUREMENT"), "mdi:white-balance-sunny",
    ),
    "precipitation": MeasureDescriptor(
        "precipitation", "precipitation", "mm",
        _dc("PRECIPITATION"), _sc("MEASUREMENT"), "mdi:weather-rainy",
    ),
    "uv_index": MeasureDescriptor(
        "uv_index", "uv_index", None,
        None, _sc("MEASUREMENT"), "mdi:white-balance-sunny",
    ),
    # --- Fließgewässer -----------------------------------------------------
    "temperature": MeasureDescriptor(
        "temperature", "water_temperature", "°C",
        _dc("TEMPERATURE"), _sc("MEASUREMENT"), "mdi:thermometer-water",
    ),
    "ph": MeasureDescriptor(
        "ph", "ph", None,
        _dc("PH"), _sc("MEASUREMENT"), "mdi:test-tube",
    ),
    "conductivity": MeasureDescriptor(
        "conductivity", "conductivity", "µS/cm",
        _dc("CONDUCTIVITY"), _sc("MEASUREMENT"), "mdi:omega",
    ),
    "oxygen": MeasureDescriptor(
        "oxygen", "oxygen", "mg/L",
        None, _sc("MEASUREMENT"), "mdi:bubble",
    ),
    "turbidity": MeasureDescriptor(
        "turbidity", "turbidity", "NTU",
        None, _sc("MEASUREMENT"), "mdi:blur-linear",
    ),
    "chlorophyll": MeasureDescriptor(
        "chlorophyll", "chlorophyll", "µg/L",
        None, _sc("MEASUREMENT"), "mdi:leaf",
    ),
    "phosphorous": MeasureDescriptor(
        "phosphorous", "phosphorous", "mg/L",
        None, _sc("MEASUREMENT"), "mdi:flask-outline",
    ),
    "ammonium": MeasureDescriptor(
        "ammonium", "ammonium", "mg/L",
        None, _sc("MEASUREMENT"), "mdi:flask-outline",
    ),
    "nitrate": MeasureDescriptor(
        "nitrate", "nitrate", "mg/L",
        None, _sc("MEASUREMENT"), "mdi:flask-outline",
    ),
}


def available_fields(snapshot: dict) -> list[str]:
    """Return the keys of measures that carry a value in the snapshot."""
    return [key for key in MEASURES if snapshot.get(key) is not None]
