"""DataUpdateCoordinator for a single Nürnberg Umweltdaten station."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import NuernbergApiClient, NuernbergApiClientConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class NuernbergDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Pulls the latest snapshot for one station on a configurable schedule."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: NuernbergApiClient,
        station_code: str,
        station_name: str,
        scan_interval_minutes: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{station_code}",
            update_interval=timedelta(minutes=scan_interval_minutes),
        )
        self.client = client
        self.station_code = station_code
        self.station_name = station_name
        self.scan_interval_minutes = scan_interval_minutes

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            resp = await self.client.get_measures(self.station_code)
        except NuernbergApiClientConnectionError as err:
            raise UpdateFailed(str(err)) from err

        if not resp.get("success"):
            raise UpdateFailed("Die API meldet keinen Erfolg.")

        message = resp.get("message") or []
        if not message:
            raise UpdateFailed("Keine Messwerte für diese Station verfügbar.")

        # Some stations (e.g. Flughafen) return several records in one
        # response - typically one air-quality and one weather record. Merge
        # them into a single flat snapshot so every available field becomes a
        # sensor. Later records win on key collisions, which is fine because
        # overlapping keys (id_station, date_entry) carry identical values.
        snapshot: dict[str, Any] = {}
        for record in message:
            if isinstance(record, dict):
                snapshot.update(record)
        return snapshot
