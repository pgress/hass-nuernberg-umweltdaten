"""The Nürnberg Umweltdaten integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import NuernbergApiClient
from .const import (
    CONF_IS_WATER,
    CONF_SCAN_INTERVAL_MIN,
    CONF_STATION_CODE,
    CONF_STATION_NAME,
    DEFAULT_SCAN_INTERVAL_AIR,
    DEFAULT_SCAN_INTERVAL_WATER,
    DOMAIN,
)
from .coordinator import NuernbergDataUpdateCoordinator
from .measures import available_fields

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


def _resolve_scan_interval(entry: ConfigEntry) -> int:
    """Pick the effective poll interval (minutes) from options or defaults."""
    is_water = entry.data.get(CONF_IS_WATER, False)
    default = (
        DEFAULT_SCAN_INTERVAL_WATER if is_water else DEFAULT_SCAN_INTERVAL_AIR
    )
    return entry.options.get(CONF_SCAN_INTERVAL_MIN, default)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Nürnberg Umweltdaten instance from a config entry."""
    session = async_get_clientsession(hass)
    client = NuernbergApiClient(session)

    coordinator = NuernbergDataUpdateCoordinator(
        hass,
        client,
        entry.data[CONF_STATION_CODE],
        entry.data.get(CONF_STATION_NAME, ""),
        _resolve_scan_interval(entry),
        entry.data.get(CONF_IS_WATER, False),
    )

    await coordinator.async_config_entry_first_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    snapshot = coordinator.data or {}
    fields = available_fields(snapshot)
    if not fields:
        raise ConfigEntryNotReady("Diese Station liefert momentan keine nutzbaren Messwerte.")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "fields": fields,
    }

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clean up when a config entry is removed (deleted).

    Deletes the long-term ``*_hist`` statistics this integration created so the
    recorder does not keep orphaned rows. Only invoked on deletion, not on
    reload, so a poll-interval change never wipes statistics history.
    """
    from .statistics import clear_statistics

    await clear_statistics(hass, entry.data[CONF_STATION_CODE])
