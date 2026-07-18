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
