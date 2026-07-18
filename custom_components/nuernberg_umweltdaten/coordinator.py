"""DataUpdateCoordinator for a single Nürnberg Umweltdaten station."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import NuernbergApiClient, NuernbergApiClientConnectionError
from .const import (
    DOMAIN,
    MAX_NEXT_REFRESH_MIN,
    MIN_NEXT_REFRESH_MIN,
    PUBLISH_DELAY_MINUTES,
    RETRY_MINUTES,
    SCHEDULE_MARGIN_MINUTES,
    STAT_BACKFILL_DAYS,
)
from .measures import MEASURE_CATEGORY, available_fields
from .statistics import import_statistics

_LOGGER = logging.getLogger(__name__)

# Time-series entries use "DD.MM.YYYY HH:mm" (local wall-clock, no timezone).
_SERIES_DATE_FORMAT = "%d.%m.%Y %H:%M"


class NuernbergDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Pulls the freshest available values for one station on a schedule.

    Hourly (air/weather) stations do not use a rigid poll interval. Instead the
    next poll is aimed a couple of minutes after the city publishes the next
    hourly value (~35 min past the hour), with short retries while the newest
    value has not advanced yet. Water stations publish every 15 minutes and
    keep the fixed interval configured by the user.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: NuernbergApiClient,
        station_code: str,
        station_name: str,
        scan_interval_minutes: int,
        is_water: bool = False,
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
        self.is_water = is_water
        # Newest measurement timestamp seen so far (naive local wall-clock).
        self._last_measure_dt: datetime | None = None
        # Whether the one-time historical backfill of statistics has run.
        self._stats_backfilled = False

    @callback
    def _schedule_refresh(self) -> None:
        """Aim the next poll at the expected next publication time."""
        if not self.is_water:
            self.update_interval = self._compute_next_interval()
        super()._schedule_refresh()

    def _compute_next_interval(self) -> timedelta:
        """Pick the timedelta until the next worthwhile poll."""
        if not self.last_update_success:
            return timedelta(minutes=RETRY_MINUTES)

        latest = self._last_measure_dt
        if latest is None:
            return timedelta(minutes=self.scan_interval_minutes)

        now = datetime.now()  # naive local, matches the API's date_entry
        next_arrival = (
            latest.replace(minute=0, second=0, microsecond=0)
            + timedelta(hours=1)
            + timedelta(minutes=PUBLISH_DELAY_MINUTES + SCHEDULE_MARGIN_MINUTES)
        )
        delta = next_arrival - now
        if delta <= timedelta(0):
            # Publication time passed without a newer value yet -> retry soon.
            return timedelta(minutes=RETRY_MINUTES)

        delta = max(delta, timedelta(minutes=MIN_NEXT_REFRESH_MIN))
        delta = min(delta, timedelta(minutes=MAX_NEXT_REFRESH_MIN))
        return delta

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
        stats_incremental: dict[str, list[tuple[datetime, float]]] = {}

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

            parsed_dt: datetime | None = None
            if date_entry:
                try:
                    parsed_dt = datetime.strptime(date_entry, _SERIES_DATE_FORMAT)
                except ValueError:
                    parsed_dt = None
            if parsed_dt is not None:
                if latest_dt is None or parsed_dt > latest_dt:
                    latest_dt = parsed_dt
                try:
                    stats_incremental.setdefault(field, []).append((parsed_dt, float(value)))
                except (TypeError, ValueError):
                    pass

        if not snapshot:
            raise UpdateFailed("Keine nutzbaren Messwerte abrufbar.")

        # Shared timestamp for the ``last_measured`` attribute.
        snapshot["date_entry"] = (
            latest_dt.strftime("%Y-%m-%d %H:%M:00")
            if latest_dt
            else discover_snapshot.get("date_entry")
        )

        self._last_measure_dt = latest_dt

        # Long-term statistics at the true measurement timestamp (no extra API
        # calls: we reuse the series we already fetched above).
        if stats_incremental:
            await import_statistics(
                self.hass, self.station_code, self.station_name, stats_incremental
            )

        # One-time backfill so the Statistics card shows history, not just the
        # moment the integration was installed.
        if not self._stats_backfilled:
            await self._backfill_statistics(fields)
            self._stats_backfilled = True

        return snapshot

    async def _backfill_statistics(self, fields: list[str]) -> None:
        """Import the recent history of each measure as long-term statistics."""
        points: dict[str, list[tuple[datetime, float]]] = {}
        for field in fields:
            cat = MEASURE_CATEGORY.get(field)
            if cat is None:
                continue
            try:
                resp = await self.client.get_series(
                    self.station_code, cat, field, days=STAT_BACKFILL_DAYS
                )
            except NuernbergApiClientConnectionError as err:
                _LOGGER.debug(
                    "Backfill fetch failed for %s/%s: %s",
                    self.station_code,
                    field,
                    err,
                )
                continue
            for entry in resp.get("message") or []:
                if not isinstance(entry, dict) or entry.get(field) is None:
                    continue
                try:
                    dt = datetime.strptime(entry["date_entry"], _SERIES_DATE_FORMAT)
                    points.setdefault(field, []).append((dt, float(entry[field])))
                except (KeyError, ValueError, TypeError):
                    continue
        if points:
            await import_statistics(
                self.hass, self.station_code, self.station_name, points
            )
