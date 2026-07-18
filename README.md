# Nürnberg Umweltdaten (Home Assistant)

Custom integration for Home Assistant that reads the public environmental data
published by the **City of Nuremberg** (Stadtentwässerung & Umweltanalytik
Nürnberg, SUN) via its JSON microservice
`https://microservices.nuernberg.de/umweltdaten/`.

## Features

- **Station picker:** during setup you choose one of the official measuring
  stations (Flughafen, Muggenhof, Frankenschnellweg, …). Several stations can
  be added independently.
- **One device per station** with the station name as device name.
- **Dynamic sensors:** only the values that the selected station actually
  reports are created. Fields that are `null` for a station are skipped, so no
  "unknown" sensors clutter your setup. A Flughafen entry therefore creates
  air-quality *and* weather sensors, while a pure weather station only exposes
  weather sensors.
- Polled every 30 minutes for air/weather stations and every 15 minutes for
  water stations by default. The interval can be tuned per station in the
  integration's options (slider, 5–1440 minutes). Changing it reloads the
  station automatically. No API key required.

## Covered measurements

| Category | Values |
|----------|--------|
| Außenluft | NO, NO₂, NOx, SO₂, O₃, O₃-8h, CO, Benzol, Toluol, Methan, THC, NMHC, PM10, PM2.5 (+ raw) |
| Wetterdaten | Lufttemperatur, Luftfeuchtigkeit, Luftdruck, Windgeschwindigkeit, Max.-Wind, Windrichtung, Globale Strahlung, Niederschlag, UV-Index |
| Fließgewässer | Wassertemperatur, pH, Leitfähigkeit, Sauerstoff, Trübung, Chlorophyll, Phosphat, Ammonium, Nitrat |

Each sensor carries `last_measured` (the station's `date_entry`) and
`station_code` as extra attributes.

## Installation (HACS)

1. Copy this repository into HACS as a custom repository
   (**Settings → Custom repositories**, category *Integration*).
2. Install **Nürnberg Umweltdaten**.
3. Restart Home Assistant.
4. Add the integration via **Settings → Devices & Services → Add integration**
   and select *Nürnberg Umweltdaten*. Pick a station – the sensors appear
   automatically.
5. Optionally adjust the polling interval via **Configure** on the integration
   card (recommended: stay near the defaults, since faster polling only
   re-fetches identical values).

## Notes

- The official portal states that data younger than seven days is still
  unverified.
- The stations *Theodor-Heuss-Brücke*, *Neumühle* and *Hüttendorf* are being
  refurbished until approximately November 2026 and may deliver stale values.
- The underlying API is undocumented; it is the same one used by the city's
  public web frontend.
