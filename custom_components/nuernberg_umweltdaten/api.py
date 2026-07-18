"""Async API client for the Nürnberg Umweltdaten microservice."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import BASE_URL

_LOGGER = logging.getLogger(__name__)


class NuernbergApiClientError(Exception):
    """Base error for the Nürnberg Umweltdaten API client."""


class NuernbergApiClientConnectionError(NuernbergApiClientError):
    """Raised when the API cannot be reached."""


class NuernbergApiClient:
    """Thin wrapper around the public JSON endpoints."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{BASE_URL}{endpoint}"
        try:
            async with self._session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as err:
            raise NuernbergApiClientConnectionError(str(err)) from err
        except TimeoutError as err:
            raise NuernbergApiClientConnectionError(str(err)) from err

    async def get_stations(self, cat: int) -> dict[str, Any]:
        """Return all stations that belong to a category (0=air,1=weather,2=water)."""
        return await self._post("get_stations/", {"cat": str(cat)})

    async def get_measures(self, station_code: str) -> dict[str, Any]:
        """Return the latest snapshot for a station (merged air/weather/water)."""
        return await self._post("get_measures/", {"type": station_code})

    async def get_series(
        self, station_code: str, cat: int, measure: str, days: int = 1
    ) -> dict[str, Any]:
        """Return the time series for a single measure of a station.

        The ``get/`` endpoint is noticeably fresher than ``get_measures/``
        (which lags roughly one hour behind). Entries for measures a station
        does not actually record come back filled with ``null``, so callers
        must pick the last non-null entry themselves.
        """
        return await self._post(
            "get/",
            {"cat": str(cat), "type": station_code, "measure": measure, "days": str(days)},
        )
