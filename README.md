# Nürnberg Umweltdaten (Home Assistant)

Custom-Integration für Home Assistant, die die öffentlichen Umweltdaten der
**Stadt Nürnberg** (Stadtentwässerung & Umweltanalytik Nürnberg, SUN) über
deren JSON-Microservice `https://microservices.nuernberg.de/umweltdaten/`
ausliest.

## Funktionen

- **Stationsauswahl:** Beim Einrichten wählst du eine der offiziellen
  Messstationen (Flughafen, Muggenhof, Frankenschnellweg, …). Mehrere Stationen
  lassen sich unabhängig voneinander hinzufügen.
- **Ein Gerät pro Station** mit dem Stationsnamen als Gerätenamen.
- **Dynamische Sensoren:** Es werden nur die Werte angelegt, die die gewählte
  Station tatsächlich liefert. Felder, die für eine Station `null` sind, werden
  übersprungen – es entstehen also keine „unknown"-Sensoren. Ein Flughafen-Eintrag
  erzeugt dadurch Luft- *und* Wettersensoren, eine reine Wetterstation nur
  Wettersensoren.
- Abruf standardmäßig alle 30 Minuten (Luft-/Wetterstationen) bzw. alle
  15 Minuten (Wasserstationen). Das Intervall ist pro Station in den Optionen
  einstellbar (Slider, 5–1440 Minuten); eine Änderung lädt die Station automatisch
  neu. Kein API-Key erforderlich.

## Erfasste Messwerte

| Kategorie | Werte |
|-----------|-------|
| Außenluft | NO, NO₂, NOx, SO₂, O₃, O₃-8h, CO, Benzol, Toluol, Methan, THC, NMHC, PM10, PM2,5 (+ roh) |
| Wetterdaten | Lufttemperatur, Luftfeuchtigkeit, Luftdruck, Windgeschwindigkeit, Max.-Wind, Windrichtung, Globale Strahlung, Niederschlag, UV-Index |
| Fließgewässer | Wassertemperatur, pH, Leitfähigkeit, Sauerstoff, Trübung, Chlorophyll, Phosphat, Ammonium, Nitrat |

Jeder Sensor trägt `last_measured` (der `date_entry` der Station) und
`station_code` als zusätzliche Attribute.

## Stationen & Messwerte

Die folgenden Lagepläne werden von der **Stadt Nürnberg** (Stadtentwässerung
und Umweltanalytik Nürnberg) veröffentlicht und zeigen die autoritativen
Standorte der Messstationen. Quelle:
[nuernberg.de/internet/umweltdaten](https://www.nuernberg.de/internet/umweltdaten/).

<table align="center">
  <tr>
    <td align="center"><img src="images/stadt_lageplan_luft.jpg" alt="Lageplan Luftmessstationen (Stadt Nürnberg)" width="420"/><br><sub>Luftmessstationen (SUN &amp; LfU)</sub></td>
    <td align="center"><img src="images/stadt_lageplan_regen.jpg" alt="Lageplan Wetter-/Niederschlagsstationen (Stadt Nürnberg)" width="420"/><br><sub>Wetter-/Niederschlagsstationen</sub></td>
  </tr>
</table>

Die folgende Tabelle zeigt, welche Werte jede Station aktuell liefert. Die
Integration erzeugt genau diese Sensoren dynamisch – `null`-Felder werden
übersprungen, sodass keine „unknown"-Entitäten entstehen.

| Code | Station | Kategorie | Messwerte |
|------|---------|-----------|-----------|
| FLH | Flughafen Nürnberg | Luft + Wetter | NO, NO₂, O₃, CO, Benzol, PM10, PM2,5 · Temp, Feuchte, Druck, Wind, Wind max, Windricht., Globalstr., Niederschlag, UV |
| FSW | Frankenschnellweg | Luft + Wetter | NO, NO₂, PM10, PM2,5 · Temp, Feuchte, Wind, Wind max, Windricht., Niederschlag |
| JKP | Jakobsplatz | Luft + Wetter | NO, NO₂, O₃, PM10, PM2,5 · Temp, Feuchte, Niederschlag |
| MGH | Muggenhof (SUN) | Luft | NO, NO₂, CO |
| MGHLFU | Muggenhof (LfU) | Luft | NO₂, O₃ |
| BHF | Bahnhof | Luft | NO₂ |
| VTS | Von-der-Tann-Straße | Luft | NO₂, CO, PM10 |
| FTS | Fürth Theresienstraße | Luft | PM10 |
| ATF | Altenfurt | Wetter | Niederschlag |
| GBD | Gebersdorf | Wetter | Niederschlag |
| WW | Wöhrder Wiese | Wetter | Niederschlag |
| WD | Worzeldorf | Wetter | Niederschlag |
| GGL | Großgründlach | Wetter | Niederschlag |
| HD | Hüttendorf | Fließgewässer | Wassertemp., Leitf., O₂, Trübung, Nitrat *(Sanierung)* |
| NM | Neumühle | Fließgewässer | Wassertemp., pH, Leitf., O₂, Trübung, Ammonium, Nitrat *(Sanierung)* |
| THB | Theodor-Heuss-Brücke | Fließgewässer | – *(Sanierung, aktuell keine nutzbaren Werte)* |

> **Hinweis:** Die Fließgewässer-Stationen *Hüttendorf*, *Neumühle* und
> *Theodor-Heuss-Brücke* werden bis ca. November 2026 erneuert und liefern
> teils veraltete bzw. keine Werte. *Muggenhof (SUN)* liegt in der
> Wissmannstraße – praktisch vor der Tür, wenn du dort wohnst.

## Installation (HACS)

[![Open your Home Assistant instance and add this repository to HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pgress&repository=hass-nuernberg-umweltdaten&category=integration)

1. Dieses Repository in HACS als benutzerdefiniertes Repository hinzufügen
   (**Einstellungen → Benutzerdefinierte Repositories**, Kategorie *Integration*).
2. **Nürnberg Umweltdaten** installieren.
3. Home Assistant neu starten.
4. Die Integration hinzufügen über **Einstellungen → Geräte & Dienste →
   Integration hinzufügen** und *Nürnberg Umweltdaten* auswählen. Eine Station
   wählen – die Sensoren erscheinen automatisch.
5. Optional das Abrufintervall anpassen über **Konfigurieren** auf der
   Integrationskarte (empfohlen: nahe den Standardwerten bleiben, da schnelleres
   Abrufen nur identische Werte erneut liefert).

## Hinweise

- Laut offiziellem Portal sind Daten, die jünger als sieben Tage sind, noch
  ungeprüft.
- Die Stationen *Theodor-Heuss-Brücke*, *Neumühle* und *Hüttendorf* werden bis
  ca. November 2026 erneuert und können veraltete Werte liefern.
- Die zugrunde liegende API ist nicht dokumentiert; es handelt sich um dieselbe
  Schnittstelle, die das öffentliche Web-Frontend der Stadt nutzt.

## Datenquelle & Urheberrecht

Sämtliche Messdaten werden von der **Stadt Nürnberg** – genauer der
*Stadtentwässerung und Umweltanalytik Nürnberg (SUN)* – über die öffentliche
Website [nuernberg.de/internet/umweltdaten/](https://www.nuernberg.de/internet/umweltdaten/)
bereitgestellt. Diese Integration nutzt denselben undokumentierten
JSON-Microservice, der auch diese Website antreibt. Es gibt keinen formellen
API-Vertrag, keinen API-Key und keine Rate-Limit-Vereinbarung; bitte nutze die
Schnittstelle fair und rufe sie nicht häufiger ab als nötig.

Die **Lagepläne** in diesem Repository (`images/stadt_lageplan_luft.jpg`,
`images/stadt_lageplan_regen.jpg`) stammen von der Stadt Nürnberg
(`nuernberg.de`) und werden hier ausschließlich zu Dokumentationszwecken
eingebunden. **Urheber- und Verwertungsrechte an diesen Plänen liegen bei der
Stadt Nürnberg.** Sie sind nicht Teil der MIT-Lizenz dieser Integration.

Die Messdaten selbst sind ebenfalls nicht von der Lizenz dieser Integration
erfasst und bleiben Eigentum der Stadt Nürnberg.

## Verwandte Projekte

Die zugrunde liegende (undokumentierte) JSON-API wurde bereits von
[`craftamap/nuernberg-umweltdaten-api`](https://github.com/craftamap/nuernberg-umweltdaten-api)
in TypeScript-Typen dokumentiert. Diese Integration baut auf derselben API auf;
vielen Dank an das Projekt für die Vorarbeit zur API-Dokumentation.

## Hinweis zur Entstehung

Diese Integration wurde vollständig mit Unterstützung von KI (Kilo / Claude)
erstellt – sämtlicher Code, die Konfigurations-Logik und die Dokumentation
sind maschinell generiert und wurden vom Autor kuratiert und geprüft. Die
zugrunde liegende API wurde durch Analyse des öffentlichen Web-Frontends der
Stadt Nürnberg (Reverse Engineering) ermittelt; sie ist nicht offiziell
dokumentiert und kann sich jederzeit ohne Vorankündigung ändern.

## Lizenz

Diese Integration steht unter der [MIT-Lizenz](LICENSE).
