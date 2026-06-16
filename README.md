# EAuto Dashboard

Ein interaktives Web-Dashboard für die Echtzeitüberwachung und Steuerung von Elektrofahrzeugen über den CAN-Bus. Das System erfasst Fahrzeugdaten, decodiert sie und zeigt sie in einem benutzerfreundlichen Dashboard an. Zusätzlich unterstützt es Firmware-Updates über OpenBLT/XCP Bootloader-Protokoll.

## Features

- **Live CAN-Bus Überwachung**: Echtzeit-Auswertung von CAN-Nachrichten
- **Dashboard Visualisierung**: Browser-basiertes Interface mit Echtzeit-Statusanzeige
- **Motor & BMS Status**: Anzeige von Motordaten und Batteriemanagementsystem-Informationen
- **CSV Export**: Datenexport mit konfigurierbarem Zeitfenster
- **Responsive Design**: Optimiert für Desktop und Tablets

## Anforderungen

- Python 3.8+
- Windows mit CAN-Adapter (PCAN, Vector, Kvaser, SLCAN)

## Installation

```bash
pip install dash plotly python-can
```

## Verwendung

```bash
# Standardwerte: interface=pcan, channel=PCAN_USBBUS3
python eauto_dashboard.py

# Mit benutzerdefinierten Parametern
python eauto_dashboard.py pcan PCAN_USBBUS1
python eauto_dashboard.py vector 0
python eauto_dashboard.py kvaser 0
python eauto_dashboard.py slcan COM3
```

Öffne dann `http://localhost:8052` im Browser.

## Projektstruktur

```
eauto_dashboard.py          # Hauptprogramm und Dashboard-Layout
├── backend/
│   ├── __init__.py
│   ├── can_bus.py          # CAN-Interface und Empfangsthread
│   ├── bootloader.py       # Firmware-Upload Logik (OpenBLT/XCP)
│   └── decoders/
│       ├── __init__.py
│       ├── can_0x505.py    # Decoder für CAN ID 0x505
│       └── can_0x560.py    # Decoder für CAN ID 0x560
└── ui/
    ├── __init__.py
    ├── banners/            # Banner-Komponenten
    │   └── __init__.py
    ├── callbacks/          # Dash Callback-Handler
    │   ├── __init__.py
    │   ├── can_banner.py   # CAN-Verbindungsstatus Banner
    │   ├── export_csv.py   # CSV-Export Callback
    │   ├── reset.py        # Daten-Reset Callback
    │   ├── snapshot.py     # Snapshot-Update Callback
    │   └── status.py       # Status-Anzeige Callback
    └── controls.py         # UI-Kontroll-Komponenten (Time Window, Upload Card)
```

## Architektur

### Backend

- **`backend/can_bus.py`**: Verwaltet die CAN-Verbindung und empfängt Nachrichten in einem separaten Thread
- **`backend/decoders/`**: Modulare Decoder für verschiedene CAN-Nachrichtenformate

### Frontend

- **`ui/controls.py`**: Wiederverwendbare UI-Komponenten (Time Window, Firmware Upload Card)
- **`ui/banners/`**: Banner-Formatierung (CAN-Status, Firmware-Update Feedback)
- **`ui/callbacks/`**: Alle Dash-Callbacks für Benutzerinteraktionen und Datenaktualisierungen

### Datenfluss

```
CAN-Bus
  ↓
can_bus.py (RX-Thread) → latest (thread-safe dict)
  ↓
Dashboard Interval (500ms)
  ↓
snapshot.py Callback → Datenspeicherung
  ↓
status.py, can_banner.py Callbacks → UI-Update
```

## Firmware-Update Prozess


## Konfigurierbare Parameter

- **Bootloader RX CAN-ID**: Standard `0x7E0` (Empfang vom Gerät)
- **Bootloader TX CAN-ID**: Standard `0x7E1` (Sendung an Gerät)
- **Program Startadresse**: Standard `0x08008000` (STM32 Applikation)
- **Time Window**: 1 min, 5 min, 30 min oder All-Time

## Lizenz

Siehe [LICENSE](LICENSE)
