# EAuto Dashboard

Ein interaktives Web-Dashboard für die Echtzeitüberwachung und Steuerung von Elektrofahrzeugen über den CAN-Bus. Das System erfasst Fahrzeugdaten, decodiert sie und zeigt sie in einem benutzerfreundlichen Dashboard an. Zusätzlich unterstützt es Firmware-Updates über OpenBLT/XCP Bootloader-Protokoll.

## Features

- **Live CAN-Bus Überwachung**: Echtzeit-Auswertung von CAN-Nachrichten mit Status-Pille in der Titelleiste (kein Adapter / getrennt / OK / Fehler)
- **BMS-Ausgänge**: Statusanzeige aller BMS GPIO-Ausgänge (CAN `0x237`)
- **Zelldaten**: Balkendiagramme der Zellspannungen (10 Module × 12 Zellen) und Zelltemperaturen (10 Module × 16 Sensoren) mit Min/Max/Δ/Avg
- **CAN-Konfiguration per UI**: Interface, Kanal und Bitrate direkt im Browser konfigurieren und verbinden/trennen
- **Firmware-Update via OpenBLT**: `.srec`-Dateien per Drag-and-Drop über XCP/CAN flashen
- **ECU-Presets**: Vordefinierte CAN-ID-Paare für BMS, Charger, HBT, MBT, SOC Display und Display-ECUs
- **CSV Export**: Aktueller Snapshot aller Werte als CSV-Datei
- **Hell/Dunkel-Theme**: Umschaltbar, Auswahl wird im Browser gespeichert

## Anforderungen

- Python 3.10+
- Windows mit CAN-Adapter (PCAN, Vector, Kvaser, IXXAT, SLCAN)
- `libopenblt.dll` im `openblt/`-Ordner (nur für Firmware-Updates erforderlich)

## Installation

```bash
pip install dash plotly python-can
```

## Verwendung

```bash
# Standardwerte: interface=pcan, channel=PCAN_USBBUS1, bitrate=500000
# Die Argumente befüllen nur die UI-Felder vor — der CAN-Adapter wird erst
# nach einem Klick auf "Verbinden" im Browser verbunden.
python eauto_dashboard.py

# Mit benutzerdefinierten Voreinstellungen für die UI-Felder
python eauto_dashboard.py pcan    PCAN_USBBUS1  500000
python eauto_dashboard.py vector  0             500000
python eauto_dashboard.py kvaser  0             500000
python eauto_dashboard.py slcan   COM3          500000
```

Öffne dann `http://localhost:8051` im Browser und klicke auf **Verbinden**, um den CAN-Adapter zu aktivieren.

Betrieb, Fehlersuche und das Hinzufügen neuer Decoder sind im [RUNBOOK](RUNBOOK.md) beschrieben.

## Projektstruktur

```
eauto_dashboard.py              # Hauptprogramm: Layout (buildLayout), Callback-Registrierung (registerCallbacks)
├── assets/
│   ├── dark.css                # Farben dunkles Theme
│   └── light.css               # Farben helles Theme
├── backend/
│   ├── __init__.py
│   ├── can_bus.py              # CanConfig, CanManager (CAN_Manager), Empfangsthread mit Reconnect
│   └── decoders/
│       ├── __init__.py         # Decoder-Registry (DECODERS / MULTI_DECODERS)
│       ├── can_0x237.py        # BMS GPIO-Ausgänge
│       ├── cell_voltages.py    # Zellspannungen 0x680 – 0x69D
│       └── cell_temperatures.py  # Zelltemperaturen 0x780 – 0x7A7
├── openblt/
│   ├── __init__.py             # Python-Wrapper für libopenblt
│   └── lib.py                  # ctypes-Bindings für libopenblt.dll
└── ui/
    ├── __init__.py
    ├── header.py               # Titelleiste: Theme-Button, CAN-Konfigurationsfelder, CAN-Status-Pille
    ├── dashboard_tab.py        # "Dashboard"-Tab: Export/Reset, Zeitfenster-Auswahl (noch ohne Funktion)
    ├── cell_data_tab.py        # "Zellen"-Tab: baut die Karten aus ui/cards/ zusammen
    ├── bootloader.py           # "Bootloader"-Tab: Firmware-Upload-Karte mit ECU-Presets
    ├── cards/
    │   ├── __init__.py
    │   ├── bms_outputs_card.py       # Statusanzeige BMS GPIO-Ausgänge
    │   ├── cell_voltage_card.py      # Balkendiagramm Zellspannungen
    │   └── cell_temperature_card.py  # Balkendiagramm Zelltemperaturen
    └── callbacks/
        ├── __init__.py
        ├── snapshot.py         # Tick → aktuellen Snapshot in dcc.Store schreiben
        ├── can_config.py       # CAN-Adapter verbinden/trennen + CAN-Status-Pille
        ├── bms_outputs.py      # BMS-Ausgänge aktualisieren
        ├── cell_data.py        # Zellspannungs-/Zelltemperatur-Charts aktualisieren
        ├── ecu_preset.py       # ECU-Preset Dropdown → CAN-ID-Felder befüllen
        ├── export_csv.py       # CSV-Export Callback
        ├── firmware_upload.py  # Firmware-Upload via OpenBLT
        ├── reset.py            # Empfangszeitstempel zurücksetzen
        ├── theme.py            # Hell/Dunkel-Theme umschalten
        ├── status.py           # BMS-/Motor-Status (derzeit nicht registriert)
        └── temperature_chart.py  # Temperatur-ADC-Diagramm (derzeit nicht registriert)
```

## Architektur

### Backend

- **`backend/can_bus.py`**: Verwaltet die CAN-Verbindung über die globale Instanz `CAN_Manager` (Klasse `CanManager`). Der Empfangsthread wird per UI-Button gestartet und gestoppt. Reconnect-Logik mit exponentiellem Backoff (3 s → 6 s → 12 s, max. 30 s).
- **`backend/decoders/`**: Modulare Decoder für CAN-Nachrichten. Zwei Registries: `DECODERS` für Single-Value-Decoder (Status/State-Paare) und `MULTI_DECODERS` für Decoder, die mehrere Keys zurückgeben.

### Frontend

- **`ui/header.py`**, **`ui/dashboard_tab.py`**, **`ui/cell_data_tab.py`**, **`ui/bootloader.py`**: Layout-Bausteine der Titelleiste und der einzelnen Tabs
- **`ui/cards/`**: Karten mit statischem Layout (Diagramme, Statuspunkte); die Werte werden von den zugehörigen Callbacks (`cell_data.py`, `bms_outputs.py`) aktualisiert
- **`ui/callbacks/`**: Alle Dash-Callbacks für Benutzerinteraktionen und Datenaktualisierungen

### Datenfluss

```
Browser → "Verbinden"-Button
  ↓
can_config.py → CAN_Manager.start()
  ↓
CAN-Bus → can_bus.py (RX-Thread) → decoders → latest (thread-safe dict)
  ↓
Dashboard Interval (500 ms)
  ↓
snapshot.py → Kopie von latest in dcc.Store
  ↓
Callbacks → UI-Update
```

## Firmware-Update Prozess

1. CAN-Adapter in der Titelleiste verbinden.
2. In den Reiter **Bootloader** wechseln.
3. ECU aus dem Dropdown wählen oder CAN-IDs manuell eingeben.
4. `.srec`-Datei in das Upload-Feld ziehen oder per Klick auswählen.
5. Dashboard prüft die Vektortabelle, stoppt den CAN-RX-Thread, öffnet `libopenblt.dll` und wartet bis zu 30 s auf den Bootloader.
6. Flash-Sequenz (entspricht BootCommander): zuerst alle Segmente löschen (Erase-Pass), dann alle schreiben (Write-Pass).
7. Nach erfolgreichem Flash startet das Gerät via `PROGRAM_RESET` neu; der CAN-RX-Thread wird 3 s später automatisch wieder gestartet.

> **Voraussetzung**: `libopenblt.dll` (und ggf. Peer-DLLs wie `peak_pcanusb.dll`) müssen im `openblt/`-Ordner liegen. Unterstützte Interfaces: pcan, kvaser, vector, ixxat, slcan.

## ECU-Presets

| ECU         | Bootloader RX | Bootloader TX |
|---|---|---|
| BMS         | `0x7E0`       | `0x7E1`       |
| Charger     | `0x66A`       | `0x7E4`       |
| HBT         | `0x66B`       | `0x7E5`       |
| MBT         | `0x66C`       | `0x7E6`       |
| SOC Display | `0x66D`       | `0x7E7`       |
| Display 1   | `0x66E`       | `0x7EE`       |
| Display 2   | `0x66F`       | `0x7EF`       |

## Konfigurierbare Parameter

- **CAN-Interface, Kanal, Bitrate**: in der Titelleiste (Bitrate 125 kbit/s, 250 kbit/s, 500 kbit/s oder 1 Mbit/s)
- **Bootloader RX CAN-ID**: ID, über die das Dashboard Befehle an den Bootloader sendet
- **Bootloader TX CAN-ID**: ID, über die der Bootloader Antworten zurücksendet

## Code-Stil

Der Python-Code folgt dem Python Coding Style aus dem Repo **Diveturtle93** (`PYTHON_CODING_STYLE.md`). Prüfung mit `py ../Diveturtle93/tools/py_stylecheck.py .` (Repo liegt neben diesem Projekt).

## Lizenz

Siehe [LICENSE](LICENSE)
