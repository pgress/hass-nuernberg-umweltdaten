"""DataUpdateCoordinator for a single Nürnberg Umweltdaten station."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import NuernbergApiClient, NuernbergApiClientConnectionError
from .const import DOMAIN
from .measures import MEASURE_CATEGORY, MEASURES, available_fields

_LOGGER = logging.getLogger(__name__)

# Time-series entries use "DD.MM.YYYY HH:mm".
_SERIES_DATE_FORMAT = "%d.%m.%Y %H:%M"


class NuernbergDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Pulls the freshest available values for one station on a schedule."""

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

    async def _discover_fields(self) -> tuple[dict[str, Any], list[str]]:
        """Use the snapshot endpoint to detect which measures a station reports."""
        resp = await self.client.get_measures(self.station_code)
        if not resp.get("success"):
            raise UpdateFailed("Die API meldet keinen Erfolg.")

        message = resp.get("message") or []
        if not message:
            raise UpdateFailed("Keine Messwerte für diese Station verfügbar.")

        snapshot: dict[str, Any] = {}
        for record in message:
            if isinstance(record, dict):
                snapshot.update(record)

        return snapshot, available_fields(snapshot)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            discover_snapshot, fields = await self._discover_fields()
        except NuernbergApiClientConnectionError as err:
            raise UpdateFailed(str(err)) from err

        if not fields:
            raise UpdateFailed("Diese Station liefert momentan keine nutzbaren Messwerte.")

        # Fetch the freshest value per measure from the time-series endpoint,
        # which is roughly one hour ahead of the snapshot endpoint. The snapshot
        # serves as a fallback if a series call fails or contains only nulls.
        snapshot: dict[str, Any] = {}
        latest_dt: datetime | None = None

        for field in fields:
            cat = MEASURE_CATEGORY.get(field)
            if cat is None:
                continue

            value: Any = None
            date_entry: str | None = None
            try:
                series_resp = await self.client.get_series(
                    self.station_code, cat, field, days=1
                )
            except NuernbergApiClientConnectionError as err:
                _LOGGER.debug("Series fetch failed for %s/%s: %s", self.station_code, field, err)
                series_resp = {}

            for entry in reversed(series_resp.get("message") or []):
                if not isinstance(entry, dict):
                    continue
                if entry.get(field) is not None:
                    value = entry[field]
                    date_entry = entry.get("date_entry")
                    break

            if value is None:
                # Fall back to the (staler) snapshot value.
                value = discover_snapshot.get(field)
                date_entry = discover_snapshot.get("date_entry")

            if value is None:
                continue

            snapshot[field] = value
            if date_entry:
                try:
                    dt = datetime.strptime(date_entry, _SERIES_DATE_FORMAT)
                except ValueError:
                    dt = None
                if dt is not None and (latest_dt is None or dt > latest_dt):
                    latest_dt = dt

        if not snapshot:
            raise UpdateFailed("Keine nutzbaren Messwerte abrufbar.")

        # Shared timestamp for the ``last_measured`` attribute.
        snapshot["date_entry"] = (
            latest_dt.strftime("%Y-%m-%d %H:%M:00") if latest_dt else discover_snapshot.get("date_entry")
        )
        return snapshot
