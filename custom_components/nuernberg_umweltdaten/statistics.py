"""Import long-term statistics at the true measurement timestamp.

The History card always stamps a sensor state with the moment Home Assistant
learned about it (i.e. the poll time). The city, however, publishes each
hourly value roughly 35 minutes past the hour, so the poll timestamp can never
match the measurement timestamp. To still expose the values at their real
times we import them as long-term statistics under dedicated ``*_hist``
statistic ids. These show up in the Statistics card / long-term statistics,
independent of the live sensor history.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant

from .const import DOMAIN, STATISTIC_SUFFIX
from .measures import MEASURES

_LOGGER = logging.getLogger(__name__)

# The API emits local wall-clock times ("DD.MM.YYYYY HH:mm") without a timezone.
_TZ = ZoneInfo("Europe/Berlin")

try:
    from homeassistant.components.recorder.statistics import (
        async_import_statistics,
    )
except ImportError:  # pragma: no cover - recorder ships with core
    async_import_statistics = None  # type: ignore[assignment]


def statistic_id(station_code: str, field: str) -> str:
    """Build the statistic id used for a station/measure pair."""
    return f"sensor.{DOMAIN}_{station_code.lower()}_{field}_{STATISTIC_SUFFIX}"


async def import_statistics(
    hass: HomeAssistant,
    station_code: str,
    station_name: str,
    points_by_field: dict[str, list[tuple[datetime, float]]],
) -> None:
    """Import measurement values as long-term statistics.

    Each ``(naive local datetime, value)`` pair becomes one statistic point
    stamped at the value's true measurement time (converted to UTC). Repeated
    imports for the same timestamp upsert harmlessly.
    """
    if async_import_statistics is None:
        return

    for field, points in points_by_field.items():
        desc = MEASURES.get(field)
        if not points or desc is None:
            continue

        stats: list[dict] = []
        for dt_local, value in sorted(points, key=lambda p: p[0]):
            if value is None:
                continue
            start = dt_local.replace(tzinfo=_TZ).astimezone(timezone.utc)
            stats.append(
                {
                    "start": start,
                    "mean": value,
                    "min": value,
                    "max": value,
                    "last": value,
                }
            )
        if not stats:
            continue

        meta = {
            "statistic_id": statistic_id(station_code, field),
            "source": DOMAIN,
            "name": f"{station_name} – {desc.translation_key}",
            "unit_of_measurement": desc.unit,
            "has_sum": False,
            "has_mean": True,
        }
        try:
            await async_import_statistics(hass, meta, stats)
        except Exception:  # noqa: BLE001
            _LOGGER.exception(
                "Failed to import statistics for %s/%s", station_code, field
            )
