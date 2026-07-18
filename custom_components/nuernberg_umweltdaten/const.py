"""Constants for the Nürnberg Umweltdaten integration."""

DOMAIN = "nuernberg_umweltdaten"

CONF_STATION_CODE = "station_code"
CONF_STATION_NAME = "station_name"
CONF_IS_WATER = "is_water"
CONF_SCAN_INTERVAL_MIN = "scan_interval_min"

# Default poll cadence per station type. Air/weather stations publish a new
# value every hour, water stations every 15 minutes - polling faster than the
# defaults only re-fetches identical values.
DEFAULT_SCAN_INTERVAL_AIR = 30      # minutes
DEFAULT_SCAN_INTERVAL_WATER = 15    # minutes
MIN_SCAN_INTERVAL_MIN = 5
MAX_SCAN_INTERVAL_MIN = 1440

# Smart scheduling for hourly (air/weather) stations. The city publishes each
# hourly value roughly 35 minutes past the hour, so the next poll is aimed a
# couple of minutes after that. While the newest value has not advanced yet the
# coordinator retries shortly instead of waiting a full hour.
PUBLISH_DELAY_MINUTES = 35
SCHEDULE_MARGIN_MINUTES = 2
RETRY_MINUTES = 5
MIN_NEXT_REFRESH_MIN = 2
MAX_NEXT_REFRESH_MIN = 70
# After this many consecutive polls where the newest measurement timestamp did
# not advance (while requests still succeed), stop the short retry loop and
# fall back to the configured scan interval to avoid hammering the API.
STALL_RETRY_LIMIT = 4

# hass.storage version/key for persisting the one-time statistics backfill so a
# restart or options-reload does not re-fetch and re-import 30 days of history.
STORAGE_VERSION = 1

# Long-term statistics. The History card always stamps a sensor state with the
# poll time, which can never match the measurement time (the city publishes
# late). To still expose values at their true timestamps we import them as
# long-term statistics under dedicated ``*_hist`` statistic ids, independent of
# the live sensor history. They show up in the Statistics card.
STATISTIC_SUFFIX = "hist"
STAT_BACKFILL_DAYS = 30

# Base URL of the public microservice used by the city's "Umweltdaten" portal.
BASE_URL = "https://microservices.nuernberg.de/umweltdaten/api/umweltdaten/"

# Mapping of the numeric id_station (returned by get_stations) to the station
# code that the remaining endpoints expect as `type`. This mirrors the lookup
# table baked into the official frontend (umweltdaten_graph.js).
STATION_ID_TO_CODE = {
    1: "FLH",
    2: "FSW",
    3: "HD",
    4: "JKP",
    5: "MGH",
    6: "NM",
    7: "THB",
    8: "ATF",
    9: "GBD",
    10: "WW",
    11: "WD",
    12: "GGL",
    14: "BHF",
    15: "VTS",
    16: "FTS",
    17: "MGHLFU",
}

MANUFACTURER = "Stadt Nürnberg"
MODEL = "Umweltdaten Station"
