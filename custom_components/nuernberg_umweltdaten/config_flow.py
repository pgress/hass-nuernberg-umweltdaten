"""Config flow for the Nürnberg Umweltdaten integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import NuernbergApiClient, NuernbergApiClientConnectionError
from .const import (
    CONF_IS_WATER,
    CONF_SCAN_INTERVAL_MIN,
    CONF_STATION_CODE,
    CONF_STATION_NAME,
    DEFAULT_SCAN_INTERVAL_AIR,
    DEFAULT_SCAN_INTERVAL_WATER,
    DOMAIN,
    MAX_SCAN_INTERVAL_MIN,
    MIN_SCAN_INTERVAL_MIN,
    STATION_ID_TO_CODE,
)
from .measures import MEASURES

_LOGGER = logging.getLogger(__name__)


async def _discover_stations(hass) -> tuple[dict[str, str], dict[str, bool]]:
    """Build a {station_code: station_name} and {station_code: is_water} mapping.

    A station counts as "water" if it is listed under category 2 (Fließgewässer).
    """
    session = async_get_clientsession(hass)
    client = NuernbergApiClient(session)
    seen: dict[str, str] = {}
    is_water: dict[str, bool] = {}

    for cat in (0, 1, 2):
        try:
            resp = await client.get_stations(cat)
        except NuernbergApiClientConnectionError:
            _LOGGER.warning("Could not fetch stations for category %s", cat)
            continue
        if not resp.get("success"):
            continue
        for station in resp.get("message", []):
            sid = station.get("id_station")
            name = station.get("name")
            code = STATION_ID_TO_CODE.get(sid)
            if code and name:
                seen[code] = name
                if cat == 2:
                    is_water[code] = True

    for code in seen:
        is_water.setdefault(code, False)

    ordered = dict(sorted(seen.items(), key=lambda kv: kv[1]))
    return ordered, is_water


async def _station_has_data(hass, code: str) -> bool:
    """Validate that a station currently returns at least one usable value."""
    session = async_get_clientsession(hass)
    client = NuernbergApiClient(session)
    resp = await client.get_measures(code)
    if not resp.get("success"):
        return False
    message = resp.get("message") or []
    if not message:
        return False
    snapshot = message[0]
    return any(snapshot.get(key) is not None for key in MEASURES)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nürnberg Umweltdaten."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "OptionsFlowHandler":
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """First step: choose a station."""
        errors: dict[str, str] = {}

        if user_input is not None and CONF_STATION_CODE in user_input:
            code = user_input[CONF_STATION_CODE]
            await self.async_set_unique_id(f"{DOMAIN}-{code}")
            self._abort_if_unique_id_configured()

            try:
                has_data = await _station_has_data(self.hass, code)
            except NuernbergApiClientConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating station %s", code)
                errors["base"] = "unknown"
            else:
                if not has_data:
                    errors["base"] = "no_data"
                else:
                    stations, is_water_map = await _discover_stations(self.hass)
                    name = stations.get(code, code)
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_STATION_CODE: code,
                            CONF_STATION_NAME: name,
                            CONF_IS_WATER: is_water_map.get(code, False),
                        },
                    )

        stations, _ = await _discover_stations(self.hass)
        if not stations:
            errors.setdefault("base", "cannot_connect")
            schema = vol.Schema({})
        else:
            schema = vol.Schema({vol.Required(CONF_STATION_CODE): vol.In(stations)})

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={"count": str(len(stations))},
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow: configure the polling interval per station."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    def _default_interval(self) -> int:
        is_water = self.config_entry.data.get(CONF_IS_WATER, False)
        default = (
            DEFAULT_SCAN_INTERVAL_WATER if is_water else DEFAULT_SCAN_INTERVAL_AIR
        )
        return self.config_entry.options.get(CONF_SCAN_INTERVAL_MIN, default)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL_MIN,
                    default=self._default_interval(),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL_MIN,
                        max=MAX_SCAN_INTERVAL_MIN,
                        step=1,
                        mode=selector.NumberSelectorMode.SLIDER,
                        unit_of_measurement="min",
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "default": str(self._default_interval()),
            },
        )
