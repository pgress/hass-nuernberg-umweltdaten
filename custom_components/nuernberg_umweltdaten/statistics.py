"""Import long-term statistics at the true measurement timestamp.

The History card always stamps a sensor state with the moment Home Assistant
learned about it (i.e. the poll time). The city, however, publishes each hourly
value roughly 35 minutes past the hour, so the poll timestamp can never match
the measurement timestamp. To still expose the values at their real times we
add them as long-term statistics under dedicated ``*:*_hist`` statistic ids
(via the external-statistics API). These show up in the Statistics card /
long-term statistics, independent of the live sensor history.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant

from .const import DOMAIN, STATISTIC_SUFFIX
from .measures import CIRCULAR_FIELDS, MEASURES

_LOGGER = logging.getLogger(__name__)

# The API emits local wall-clock times ("DD.MM.YYYY HH:mm") without a timezone.
_TZ = ZoneInfo("Europe/Berlin")

try:
    from homeassistant.components.recorder.statistics import (
        StatisticMeanType,
        async_add_external_statistics,
        async_list_statistic_ids,
    )
except ImportError:  # pragma: no cover - recorder ships with core
    async_add_external_statistics = None  # type: ignore[assignment]
    async_list_statistic_ids = None  # type: ignore[assignment]
    StatisticMeanType = None  # type: ignore[assignment]

try:
    from homeassistant.components.recorder.util import get_instance
except ImportError:  # pragma: no cover - recorder ships with core
    get_instance = None  # type: ignore[assignment]


def statistic_id(station_code: str, field: str) -> str:
    """Build the external statistic id used for a station/measure pair.

    External statistic ids use a ``<source>:<statistic>`` layout where both
    parts are slugs; the leading part must equal the metadata ``source``.
    """
    return f"{DOMAIN}:{station_code.lower()}_{field}_{STATISTIC_SUFFIX}"


async def import_statistics(
    hass: HomeAssistant,
    station_code: str,
    station_name: str,
    points_by_field: dict[str, list[tuple[datetime, float]]],
) -> datetime | None:
    """Add measurement values as long-term statistics.

    Each ``(naive local datetime, value)`` pair becomes one statistic point
    stamped at the value's true measurement time (converted to UTC). Repeated
    imports for the same timestamp upsert harmlessly. Returns the newest local
    measurement timestamp that was actually imported (or ``None``).
    """
    if async_add_external_statistics is None or StatisticMeanType is None:
        return None

    imported_max: datetime | None = None

    for field, points in points_by_field.items():
        desc = MEASURES.get(field)
        if not points or desc is None:
            continue
        # Circular quantities have no meaningful arithmetic aggregation in HA.
        if field in CIRCULAR_FIELDS:
            continue

        stats: list[dict] = []
        field_max: datetime | None = None
        for dt_local, value in sorted(points, key=lambda p: p[0]):
            if value is None:
                continue
            start = dt_local.replace(tzinfo=_TZ).astimezone(timezone.utc)
            stats.append(
                {
                    "start": start,
                    "state": value,
                    "mean": value,
                    "min": value,
                    "max": value,
                }
            )
            if field_max is None or dt_local > field_max:
                field_max = dt_local
        if not stats:
            continue

        meta = {
            "statistic_id": statistic_id(station_code, field),
            "source": DOMAIN,
            "name": f"{station_name} – {desc.translation_key}",
            "unit_of_measurement": desc.unit,
            # No unit conversion: keep the values as published by the city.
            "unit_class": None,
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
        }
        try:
            async_add_external_statistics(hass, meta, stats)
        except Exception:  # noqa: BLE001
            _LOGGER.exception(
                "Failed to import statistics for %s/%s", station_code, field
            )
            continue
        if field_max is not None and (imported_max is None or field_max > imported_max):
            imported_max = field_max

    return imported_max


async def clear_statistics(hass: HomeAssistant, station_code: str) -> None:
    """Delete all long-term statistics owned by this station.

    Called from ``async_remove_entry`` (entry deletion only, not reload) so the
    recorder does not keep orphaned ``*_hist`` rows after the integration is
    removed. Silently no-ops when the recorder is unavailable.
    """
    if async_list_statistic_ids is None or get_instance is None:
        return
    try:
        all_ids = await async_list_statistic_ids(hass)
    except Exception:  # noqa: BLE001
        _LOGGER.debug("Could not list statistic ids for cleanup", exc_info=True)
        return

    prefix = f"{DOMAIN}:{station_code.lower()}_"
    mine = [
        s["statistic_id"]
        for s in all_ids
        if s.get("source") == DOMAIN
        and isinstance(s.get("statistic_id"), str)
        and s["statistic_id"].startswith(prefix)
    ]
    if not mine:
        return
    try:
        get_instance(hass).async_clear_statistics(mine)
    except Exception:  # noqa: BLE001
        _LOGGER.debug("Could not clear statistics for %s", station_code, exc_info=True)
