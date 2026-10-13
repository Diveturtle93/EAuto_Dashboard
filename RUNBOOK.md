# EAuto Dashboard — Entwickler-Runbook

## Wann dieses Runbook verwenden

- Dashboard starten oder stoppen
- CAN-Interface verbinden (PCAN, Vector, Kvaser, IXXAT, slcan, …)
- CAN-Status in der Titelleiste deuten und Verbindungsprobleme diagnostizieren
- Daten exportieren oder Firmware-Update auslösen
- Neuen CAN-Decoder ergänzen
- Setup an einen anderen Entwickler übergeben

---

## Voraussetzungen

| Anforderung | Details |
|---|---|
| Python | 3.10 oder neuer |
| Abhängigkeiten | `pip install dash plotly python-can` |
| CAN-Adapter | PCAN-USB, Vector, Kvaser, IXXAT oder slcan-kompatibler Adapter |
| Treiber | Herstellertreiber vor dem Start installieren |
| Betriebssystem | Windows (primäres Ziel); Linux funktioniert mit `socketcan` |
| libopenblt.dll | Nur für Firmware-Updates: DLL (+ Peer-DLLs) in den `openblt/`-Ordner kopieren |

Setup prüfen:

```bash
python -c "import can; print(can.__version__)"
python -c "import dash; print(dash.__version__)"
```

---

## Dashboard starten

```bash
# Standard: Voreinstellung pcan / PCAN_USBBUS1 / 500 kbit/s in der UI
python eauto_dashboard.py

# Eigene Voreinstellung für die UI-Felder
python eauto_dashboard.py pcan    PCAN_USBBUS1  500000
python eauto_dashboard.py vector  0             500000
python eauto_dashboard.py kvaser  0             500000
python eauto_dashboard.py slcan   COM3          500000

# Im Browser öffnen
# http://localhost:8051
```

Die Kommandozeilenargumente befüllen nur die Eingabefelder in der Titelleiste vor. Die Bitrate muss einer der Werte aus dem Dropdown sein (125000, 250000, 500000, 1000000). Der CAN-Adapter wird **nicht automatisch verbunden** — erst nach Klick auf **Verbinden** im Browser startet der RX-Thread.

Erfolgreicher Start (ohne Argumente) sieht so aus:

```
============================================================
  EAuto Live Dashboard (Windows)
  Standardwerte: pcan / PCAN_USBBUS1 @ 500000 bps
  CAN-Adapter bitte im Browser verbinden.
  Dashboard: http://localhost:8051
============================================================
```

Nach Klick auf **Verbinden** im Browser:

```
[CAN] Manager started: pcan/PCAN_USBBUS1 @ 500000 bps
[CAN] Connected: interface=pcan, channel=PCAN_USBBUS1, bitrate=500000
```

Das Dashboard ist nur lokal erreichbar (`127.0.0.1`).

---

## Dashboard stoppen

Im Terminal `Strg+C` drücken. Der CAN-RX-Thread ist ein Daemon-Thread und beendet sich automatisch.

Alternativ: Im Browser auf **Trennen** klicken, um nur den CAN-Thread zu stoppen, ohne den Prozess zu beenden.

---

## Aufbau der Oberfläche

| Bereich | Inhalt |
|---|---|
| Titelleiste | CAN-Konfiguration (Interface, Kanal, Bitrate, **Verbinden**/**Trennen**), CAN-Status-Pille, Hell/Dunkel-Umschalter |
| Reiter **Dashboard** | **Export CSV**, **Reset**, Statusanzeige aller BMS GPIO-Ausgänge (CAN `0x237`) |
| Reiter **Zellen** | Balkendiagramme Zellspannungen (10 Module × 12 Zellen) und Zelltemperaturen (10 Module × 16 Sensoren) mit Min/Max/Δ/Avg |
| Reiter **Bootloader** | Firmware-Upload über OpenBLT |

Die Anzeige wird alle 500 ms aus dem aktuellen Snapshot aktualisiert.

---

## CAN-Interface verbinden und trennen

Die CAN-Konfiguration befindet sich in der **Titelleiste** des Dashboards:

1. Interface aus dem Dropdown wählen (pcan, vector, kvaser, slcan, ixxat, usb2can, socketcan).
2. Kanal und Bitrate einstellen.
3. Auf **Verbinden** klicken — es wird ein synchroner Verbindungstest durchgeführt. Schlägt er fehl, erscheint sofort „Kein Adapter gefunden: …“.
4. Bei Erfolg wechselt der Button zu **Trennen** und die Konfigurationsfelder werden ausgeblendet.

---

## CAN-Interface-Fehlersuche

### CAN-Status-Pille in der Titelleiste

| Anzeige | Bedeutung |
|---|---|
| Grau „Kein Adapter“ | Kein Adapter verbunden (noch nicht auf **Verbinden** geklickt oder getrennt) |
| Gelb „Adapter getrennt“ | Adapter war verbunden, die Verbindung ist abgerissen; der RX-Thread versucht neu zu verbinden |
| Grün „CAN OK“ | Verbunden; entweder noch kein Frame empfangen oder letzter Frame jünger als 3 s |
| Rot „CAN Fehler (N s)“ | Verbunden, aber seit N > 3 s kein Frame mehr empfangen |

**Schritt 1 — Terminal-Ausgabe prüfen.**
```
[CAN] Cannot open pcan/PCAN_USBBUS1: ...  -- retrying in 3 s
[CAN] Bus error: ...  -- reconnecting in 3 s
```
Der Thread versucht die Verbindung automatisch mit exponentiellem Backoff (3 s → 6 s → 12 s, max. 30 s).

**Schritt 2 — Adapter im Betriebssystem prüfen.**

| Adapter | Prüfung |
|---|---|
| PCAN | PCAN-View öffnen; Gerät muss erscheinen |
| Vector | Vector Hardware Config öffnen; Kanal zuweisen |
| Kvaser | Kvaser Hardware öffnen; Gerät in der Liste prüfen |
| slcan | COM-Port im Geräte-Manager prüfen |

**Schritt 3 — Bitrate mit dem Bus abgleichen.**
Voreinstellung ist 500 kbit/s. Wenn das Fahrzeug eine andere Bitrate verwendet, **Trennen**, die korrekte Bitrate aus dem Dropdown wählen und neu verbinden.

**Schritt 4 — Abschlusswiderstand prüfen.**
Ein CAN-Bus braucht an beiden Enden je 120 Ω. Fehlende Terminierung führt zu sporadischem oder keinem Empfang.

**Schritt 5 — Empfangszeitstempel zurücksetzen.**
Im Reiter **Dashboard** auf **Reset** klicken. Das setzt den Zeitstempel des letzten Frames zurück (Pille zeigt wieder „CAN OK“, bis neue Frames kommen oder 3 s ohne Frame vergangen sind), ohne den Prozess neu zu starten. Die zuletzt empfangenen Messwerte bleiben erhalten.

---

## Datenexport

Im Reiter **Dashboard** auf **Export CSV** klicken. Die Datei heißt `EAuto_JJJJMMTT_HHMMSS.csv` und wird über den Browser heruntergeladen.

Die CSV enthält zwei Spalten (`key`, `value`) mit dem aktuellen Snapshot, also dem jeweils letzten empfangenen Wert jedes Keys (z. B. `cell_v_m0_c0`, `sys_ams_ok`, `last_rx_ms`). Listen werden mit `;` getrennt in eine Zelle geschrieben. Ein Zeitverlauf wird nicht exportiert.

---

## Firmware-Update (OpenBLT via XCP/CAN)

### Voraussetzung

`libopenblt.dll` (und ggf. Peer-DLLs wie `peak_pcanusb.dll`) müssen im `openblt/`-Ordner liegen. Ohne die DLL meldet das Dashboard beim Upload-Versuch einen Fehler.

Unterstützte Interfaces: pcan, kvaser, vector, ixxat, slcan. Bei pcan wird der Kanal aus `PCAN_USBBUSx` übernommen, bei den anderen muss der Kanal eine Zahl sein.

### Ablauf

1. CAN-Adapter in der Titelleiste verbinden.
2. In den Reiter **Bootloader** wechseln.
3. ECU aus dem **Steuergerät**-Dropdown wählen — die CAN-IDs werden automatisch eingetragen.
4. `.srec`-Datei per Drag-and-Drop oder Klick hochladen.
5. Dashboard prüft die Vektortabelle der Firmware, stoppt den CAN-RX-Thread, öffnet `libopenblt` und wartet bis zu 30 s auf den Bootloader.
6. Flash-Sequenz (entspricht BootCommander): zuerst alle Segmente löschen, dann alle schreiben. Der Fortschritt wird mit zwei Balken angezeigt.
7. Nach Abschluss startet das Gerät via `PROGRAM_RESET` neu. Der RX-Thread wird 3 s später wieder gestartet.

Ergebnis bei Erfolg:
```
Firmware erfolgreich übertragen!  Datei: firmware.srec · 1 Segment(e) · 53248 Bytes
  Segment 1: 0x08003000 – 0x0800FFFF  (53248 Bytes)
  Vektortabelle @ 0x08003000:  SP=0x20020000 ✓  RV=0x080031C1 ✓
Das Gerät wird via PROGRAM_RESET automatisch neu gestartet.
```

### ECU-Presets

| ECU         | Bootloader RX | Bootloader TX |
|---|---|---|
| BMS         | `0x7E0`       | `0x7E1`       |
| Charger     | `0x66A`       | `0x7E4`       |
| HBT         | `0x66B`       | `0x7E5`       |
| MBT         | `0x66C`       | `0x7E6`       |
| SOC Display | `0x66D`       | `0x7E7`       |
| Display 1   | `0x66E`       | `0x7EE`       |
| Display 2   | `0x66F`       | `0x7EF`       |

Die Presets stehen in `ECU_PRESETS` in `ui/bootloader.py`.

### Fehlermeldungen

| Meldung | Ursache | Maßnahme |
|---|---|---|
| `libopenblt.dll nicht gefunden` | DLL fehlt im `openblt/`-Ordner | DLL hineinkopieren |
| `CAN-Bus nicht verbunden` | CAN nicht verbunden | Zuerst **Verbinden** klicken |
| `Interface '…' wird von OpenBLT nicht unterstützt` | Interface ohne OpenBLT-Treiber (z. B. usb2can, socketcan) | Unterstützten Adapter verwenden |
| `Ungültige CAN-ID eingegeben` | RX/TX-ID ist keine Hex- (`0x…`) oder Dezimalzahl | Eingabe korrigieren |
| `Flash-Vorgang läuft bereits` | Upload während eines laufenden Flash-Vorgangs | Abschluss abwarten |
| `Firmware-Datei konnte nicht geladen werden` | Datei ist kein gültiges S-Record | `.srec`-Datei prüfen |
| `Keine Firmware-Segmente in der Datei gefunden` | S-Record ohne Daten | Build prüfen |
| `Vektortabelle der Firmware ist ungültig` | Firmware für falsche Startadresse kompiliert | Linker-Startadresse prüfen |
| `Bootloader nach 30 s nicht erreichbar` | Gerät nicht im Bootloader-Modus | Power-Cycle oder Reset während des Wartens |
| `Flash-Löschung fehlgeschlagen` | Timeout bei `PROGRAM_CLEAR` | Bitrate prüfen; Gerät im Bootloader? |
| `Schreiben fehlgeschlagen` | Fehler bei `PROGRAM` | Bitrate und Verkabelung prüfen, erneut flashen |

---

## Neuen CAN-Decoder hinzufügen

### Single-Value-Decoder (Status + State)

1. `backend/decoders/can_0xNNN.py` nach dem Python Coding Style (Diveturtle93) anlegen, Funktionsabschnitt:

```python
# CAN 0xNNN dekodieren, Rueckgabe: (statusCode, stateString)
#-----------------------------------------------------------------------
def decode0xNNN (data):
	if len(data) < 1:
		return None

	return data[0], "Running" if data[0] == 1 else "Idle"
#-----------------------------------------------------------------------
```

2. In `backend/decoders/__init__.py` registrieren (Import im Abschnitt `Einfuegen der eigenen Module`, Eintrag im Abschnitt `Variablen definieren`):

```python
from .can_0xNNN import decode0xNNN

DECODERS[0xNNN] = (decode0xNNN, "mein_status_code", "mein_state")
```

3. Initialwerte in `latest` in `eauto_dashboard.py` ergänzen:

```python
latest = dict(
	last_rx_ms=0,
	can_adapter_connected=False,
	_can_rx_ts={},
	mein_status_code=None,
	mein_state="Unknown",
)
```

4. Anzeige als Karte in `ui/cards/` und Callback in `ui/callbacks/` anlegen, Karte im Layout (`buildLayout()` in `eauto_dashboard.py`) einbinden und Callback in `registerCallbacks()` registrieren. Vorlage: `bms_outputs_card.py` + `bms_outputs.py`.

### Multi-Value-Decoder (mehrere Keys)

```python
# backend/decoders/__init__.py
from .can_0xNNN import decode0xNNN

MULTI_DECODERS[0xNNN] = decode0xNNN											# decode0xNNN(data) -> {key: value, ...}
```

### Belegte CAN-IDs

| CAN-ID | Decoder | Keys |
|---|---|---|
| `0x237` | `can_0x237.py` | BMS GPIO-Ausgänge (`sys_*`, `hc_*`, `led_*`, `komfort_*`, `gpio_counter`) |
| `0x680` – `0x69D` | `cell_voltages.py` | Zellspannungen `cell_v_m<Modul>_c<Zelle>` |
| `0x780` – `0x7A7` | `cell_temperatures.py` | Zelltemperaturen `cell_t_m<Modul>_s<Sensor>` |

---

## Code-Stil prüfen

Der Python-Code folgt dem Python Coding Style aus dem Repo **Diveturtle93** (`PYTHON_CODING_STYLE.md`). Prüfung (Repo liegt neben diesem Projekt):

```bash
py ../Diveturtle93/tools/py_stylecheck.py .
```

`openblt/` ist per `.stylecheck` ausgeschlossen.

---

## Projektstruktur

```
eauto_dashboard.py              Einstiegspunkt: Layout (buildLayout), Callback-Registrierung (registerCallbacks)
backend/
  can_bus.py                    CanConfig, CanManager (CAN_Manager), CAN-RX-Thread mit Reconnect/Backoff
  decoders/
    __init__.py                 Decoder-Registries (DECODERS / MULTI_DECODERS)
    can_0x237.py                BMS GPIO-Ausgänge
    cell_voltages.py            Zellspannungen 0x680 – 0x69D
    cell_temperatures.py        Zelltemperaturen 0x780 – 0x7A7
openblt/
  __init__.py                   Python-Wrapper für libopenblt
  lib.py                        ctypes-Bindings für libopenblt.dll
ui/
  header.py                     Titelleiste: CAN-Konfiguration, CAN-Status-Pille, Theme-Button
  dashboard_tab.py              Reiter "Dashboard": Export/Reset
  cell_data_tab.py              Reiter "Zellen": setzt die Zell-Karten zusammen
  bootloader.py                 Reiter "Bootloader": Firmware-Upload-Karte mit ECU-Presets
  cards/
    bms_outputs_card.py         Statusanzeige BMS GPIO-Ausgänge
    cell_voltage_card.py        Balkendiagramm Zellspannungen
    cell_temperature_card.py    Balkendiagramm Zelltemperaturen
  callbacks/
    snapshot.py                 Tick -> aktuellen Snapshot in dcc.Store
    can_config.py               CAN-Adapter verbinden/trennen, CAN-Status-Pille
    bms_outputs.py              BMS-Ausgänge aktualisieren
    cell_data.py                Zell-Charts und Statistik aktualisieren, Chart-Farben je Theme
    ecu_preset.py               ECU-Dropdown -> CAN-ID-Felder befüllen
    export_csv.py               CSV-Download
    firmware_upload.py          Firmware-Flash-Sequenz via libopenblt
    reset.py                    Empfangszeitstempel zurücksetzen
    theme.py                    Hell/Dunkel umschalten
    status.py                   (derzeit nicht registriert) BMS-/Motor-Status
    temperature_chart.py        (derzeit nicht registriert) Temperatur-ADC-Diagramm
assets/
  dark.css, light.css           Farben der beiden Themes
```

---

## Eskalation

| Symptom | Maßnahme |
|---|---|
| CAN-Frames empfangen, dekodierte Werte falsch | Decoder in `backend/decoders/` prüfen |
| Status-Pille springt zwischen „CAN OK“ und „CAN Fehler“ | Sendeintervall der Steuergeräte prüfen (> 3 s?); `last_rx_ms`-Update in `can_bus.py` prüfen |
| Anzeige bleibt leer, obwohl Frames ankommen | CAN-ID im Decoder registriert? Terminal auf `[CAN] Decoder error` prüfen |
| Dashboard lädt nicht | Terminal auf Python-Import-Fehler prüfen |
| Firmware-Upload reagiert nicht | `registerFirmwareUploadCallback(app, CAN_Manager, latest, lock)` muss in `registerCallbacks()` in `eauto_dashboard.py` aufgerufen werden |
| libopenblt-Fehler beim Flash | DLL im `openblt/`-Ordner prüfen; bei PCAN auch `peak_pcanusb.dll` prüfen |
