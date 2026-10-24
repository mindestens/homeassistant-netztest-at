# Netztest AT – Home Assistant integration for the RTR-Netztest

**[🇦🇹 Deutsche Version weiter unten](#deutsch)**

Unofficial Home Assistant integration for the Austrian RTR-Netztest. Measures your internet speed using only the official
client of the Austrian regulator RTR – results go to RTR only, never to commercial speed-test providers.

> This project is **not** affiliated with, endorsed or reviewed by the Rundfunk und Telekom Regulierungs-GmbH (RTR-GmbH).

## Why this integration?

Common speed-test integrations send every result, including your IP address, to commercial providers, usually based abroad.
This integration was built for data protection reasons: it uses only the official RTR-Netztest of the Austrian
Rundfunk und Telekom Regulierungs-GmbH (RTR). Results go to RTR only, a public authority subject to Austrian law and the GDPR.
RTR chooses the test server; for Austrian connections this is normally a server in Vienna.

**Good to know:** like every RTR-Netztest, each test is published anonymised as open data (truncated IP address, provider,
no location). RTR keeps the full IP address for at most 6 months. See RTR's
[privacy policy and terms of use](https://www.netztest.at/en/tc).

## Features

- Download, upload, ping (median, min, max) and jitter
- Contract compliance in % for download and upload (optional, enter your contract values)
- Test server, provider, link to the result on netztest.at, time of the last test
- Tests at fixed times you choose (1–24 per day, at least 30 minutes apart), optional random delay
- "Run test" button and a "Test running" sensor; service `netztest_at.run_test` for automations
- Warning (sensor and repair notice) if RTR assigns a test server outside Austria
- Waits while another speed-test program is running on the same system (e.g. Speedtest CLI, LibreSpeed CLI, iperf3),
  so two measurements never share the line
- User interface in German and English

## Requirements

- Home Assistant 2026.9 or newer (Home Assistant OS, Container or Core)
- CPU architecture x86_64 or aarch64 (64-bit ARM, e.g. Raspberry Pi 4/5)
- Agreement to RTR's privacy policy and terms of use during setup

## Installation

### HACS (custom repository)

1. In Home Assistant open **HACS**.
2. Menu **⋮** → **Custom repositories**.
3. Repository: `https://github.com/mindestens/homeassistant-netztest-at`, type: **Integration** → **Add**.
4. Search for **Netztest AT**, open it and click **Download**.
5. Restart Home Assistant.

### Manual

1. Download the source code of the [latest release](https://github.com/mindestens/homeassistant-netztest-at/releases/latest).
2. Copy the folder `custom_components/netztest_at` into the `custom_components` folder of your Home Assistant configuration.
3. Restart Home Assistant.

## Setup

**Settings → Devices & services → Add integration → Netztest AT**

| Field | Description |
|---|---|
| Run tests automatically | Off = tests only via button or service |
| Test times | e.g. `03:00, 19:00, 22:00` – there is no default |
| Random delay | 0–15 minutes; spreads the load on RTR's servers |
| Contract download / upload | optional, in Mbit/s; enables the compliance sensors |
| Consent | required: agreement to RTR's privacy policy and terms of use |

All values can be changed later under **Configure**.

**Tip:** test both at night (reference value) and in the evening between 19:00 and 22:00 – that is when bottlenecks at the
provider usually show up.

## Entities

| Entity | Description |
|---|---|
| `sensor.netztest_at_download` / `_upload` | Mbit/s |
| `sensor.netztest_at_ping` / `_ping_min` / `_ping_max` / `_jitter` | ms |
| `sensor.netztest_at_download_plan_compliance` / `_upload_plan_compliance` | % of the contract value (only if set) |
| `sensor.netztest_at_server` / `_provider` / `_result_url` / `_last_test` | test details |
| `binary_sensor.netztest_at_running` | on while a test is running |
| `binary_sensor.netztest_at_server_abroad` | on if the last test server was not recognised as Austrian |
| `button.netztest_at_run_test` | start a test now |

## How it works

The integration runs the official RTR-Netztest client
([Open-RMBT, `clientC`](https://github.com/rtr-nettest/open-rmbt-client-cli), Apache 2.0) as a separate process; Home
Assistant itself only reads the result. The client is built **unmodified** from RTR's source by this repository's
[release workflow](.github/workflows/release.yml) as a static Linux binary and attached to each release together with
`SHA256SUMS`. During setup the integration downloads the binary matching its version and CPU architecture and verifies its
SHA-256 checksum before using it. No binary is stored in the repository.

A test takes about 30 seconds; the data volume depends on the speed (roughly 120 MB at 100 Mbit/s).

## Limitations

- No latency under load / bufferbloat: the RTR method measures ping only before the transfer.
- Other speed tests are only detected as separate programs; tests that run inside Home Assistant itself (pure Python)
  are not recognised – schedule them at different times.
- Automatic measurements are for monitoring. For a dispute with your provider, RTR offers the browser-based
  "zertifizierte Messung" (certified measurement) on [netztest.at](https://www.netztest.at).

## License

Apache License 2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE). The RTR-Netztest logo and wordmark are not used.
Open data of the RTR-Netztest: CC BY 4.0, source: RTR-Netztest.

---

<a id="deutsch"></a>

# Netztest AT – Home-Assistant-Integration für den RTR-Netztest (Deutsch)

Inoffizielle Home-Assistant-Integration für den RTR-Netztest (Österreich). Misst die Internetgeschwindigkeit ausschließlich
mit dem offiziellen Client der Regulierungsbehörde RTR – Ergebnisse gehen nur an die RTR, keine Weitergabe an kommerzielle
Speedtest-Anbieter.

> Dieses Projekt ist **nicht** mit der Rundfunk und Telekom Regulierungs-GmbH (RTR-GmbH) verbunden und wird von ihr weder
> unterstützt noch geprüft.

## Warum diese Integration?

Gängige Speedtest-Integrationen übermitteln jedes Ergebnis samt IP-Adresse an kommerzielle Anbieter, meist mit Sitz im
Ausland. Diese Integration wurde aus Datenschutzgründen entwickelt: Sie verwendet ausschließlich den offiziellen RTR-Netztest
der österreichischen Rundfunk und Telekom Regulierungs-GmbH (RTR). Die Ergebnisse gehen nur an die RTR, die als Behörde dem
österreichischen Recht und der DSGVO unterliegt. Den Testserver wählt die RTR; für österreichische Anschlüsse ist das in der
Regel ein Server in Wien.

**Gut zu wissen:** Wie jeder RTR-Netztest wird auch jeder Test dieser Integration anonymisiert als Open Data veröffentlicht
(gekürzte IP-Adresse, Provider, keine Position). Die vollständige IP-Adresse speichert die RTR höchstens 6 Monate. Siehe
[Datenschutzerklärung und Nutzungsbedingungen](https://www.netztest.at/de/tc) der RTR.

## Funktionen

- Download, Upload, Ping (Median, min, max) und Jitter
- Vertragserfüllung in % für Download und Upload (optional, Vertragswerte eingeben)
- Testserver, Provider, Link zum Ergebnis auf netztest.at, Zeitpunkt des letzten Tests
- Tests zu selbst gewählten festen Uhrzeiten (1–24 pro Tag, mindestens 30 Minuten Abstand), optionale Zufallsverzögerung
- Knopf „Test starten“ und Sensor „Test läuft“; Dienst `netztest_at.run_test` für Automationen
- Warnung (Sensor und Reparatur-Hinweis), wenn die RTR einen Testserver außerhalb Österreichs zuteilt
- Wartet, solange auf demselben System ein anderes Speedtest-Programm läuft (z. B. Speedtest CLI, LibreSpeed CLI,
  iperf3) – zwei Messungen teilen sich nie die Leitung
- Oberfläche auf Deutsch und Englisch

## Voraussetzungen

- Home Assistant 2026.9 oder neuer (Home Assistant OS, Container oder Core)
- Prozessor x86_64 oder aarch64 (64-Bit-ARM, z. B. Raspberry Pi 4/5)
- Zustimmung zu Datenschutzerklärung und Nutzungsbedingungen der RTR bei der Einrichtung

## Installation

### HACS (benutzerdefiniertes Repository)

1. In Home Assistant **HACS** öffnen.
2. Menü **⋮** → **Benutzerdefinierte Repositories**.
3. Repository: `https://github.com/mindestens/homeassistant-netztest-at`, Typ: **Integration** → **Hinzufügen**.
4. Nach **Netztest AT** suchen, öffnen und **Herunterladen** klicken.
5. Home Assistant neu starten.

### Manuell

1. Den Quellcode des [aktuellen Release](https://github.com/mindestens/homeassistant-netztest-at/releases/latest) herunterladen.
2. Den Ordner `custom_components/netztest_at` in den Ordner `custom_components` der Home-Assistant-Konfiguration kopieren.
3. Home Assistant neu starten.

## Einrichtung

**Einstellungen → Geräte & Dienste → Integration hinzufügen → Netztest AT**

| Feld | Beschreibung |
|---|---|
| Automatisch testen | Aus = Tests nur per Knopf oder Dienst |
| Uhrzeiten der Tests | z. B. `03:00, 19:00, 22:00` – es gibt keine Vorgabe |
| Zufällige Verzögerung | 0–15 Minuten; verteilt die Last auf den RTR-Servern |
| Vertrag Download / Upload | optional, in Mbit/s; aktiviert die Sensoren zur Vertragserfüllung |
| Zustimmung | Pflicht: Zustimmung zu Datenschutzerklärung und Nutzungsbedingungen der RTR |

Alle Werte lassen sich später unter **Konfigurieren** ändern.

**Tipp:** Sowohl nachts (Referenzwert) als auch abends zwischen 19 und 22 Uhr testen – dann zeigen sich Engpässe beim
Provider am ehesten.

## Entitäten

| Entität | Beschreibung |
|---|---|
| `sensor.netztest_at_download` / `_upload` | Mbit/s |
| `sensor.netztest_at_ping` / `_ping_min` / `_ping_max` / `_jitter` | ms |
| `sensor.netztest_at_download_plan_compliance` / `_upload_plan_compliance` | % vom Vertragswert (nur wenn angegeben) |
| `sensor.netztest_at_server` / `_provider` / `_result_url` / `_last_test` | Details zum Test |
| `binary_sensor.netztest_at_running` | an, während ein Test läuft |
| `binary_sensor.netztest_at_server_abroad` | an, wenn der letzte Testserver nicht als österreichisch erkannt wurde |
| `button.netztest_at_run_test` | Test sofort starten |

## Funktionsweise

Die Integration startet den offiziellen RTR-Netztest-Client
([Open-RMBT, `clientC`](https://github.com/rtr-nettest/open-rmbt-client-cli), Apache 2.0) als eigenen Prozess; Home Assistant
liest nur das Ergebnis. Der Client wird vom [Release-Workflow](.github/workflows/release.yml) dieses Repositorys
**unverändert** aus dem Quellcode der RTR als statisches Linux-Programm gebaut und mit `SHA256SUMS` an jedes Release
angehängt. Bei der Einrichtung lädt die Integration das zu ihrer Version und zum Prozessor passende Programm herunter und
prüft die SHA-256-Prüfsumme, bevor sie es verwendet. Im Repository selbst liegt kein Programm.

Ein Test dauert etwa 30 Sekunden; die Datenmenge hängt von der Geschwindigkeit ab (bei 100 Mbit/s rund 120 MB).

## Einschränkungen

- Kein Ping unter Last / Bufferbloat: Das RTR-Verfahren misst den Ping nur vor der Übertragung.
- Andere Speedtests werden nur als eigene Programme erkannt; Tests, die direkt in Home Assistant laufen (reines Python),
  nicht – diese zu anderen Uhrzeiten einplanen.
- Automatische Messungen dienen der Überwachung. Für eine Beschwerde beim Provider bietet die RTR auf
  [netztest.at](https://www.netztest.at) die „zertifizierte Messung“ im Browser an.

## Lizenz

Apache License 2.0, siehe [LICENSE](LICENSE) und [NOTICE](NOTICE). Logo und Schriftzug des RTR-Netztests werden nicht
verwendet. Open Data des RTR-Netztests: CC BY 4.0, Quelle: RTR-Netztest.
