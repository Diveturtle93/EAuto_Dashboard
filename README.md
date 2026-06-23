# EAuto Dashboard

Ein interaktives Web-Dashboard für die Echtzeitüberwachung und Steuerung von Elektrofahrzeugen über den CAN-Bus. Das System erfasst Fahrzeugdaten, decodiert sie und zeigt sie in einem benutzerfreundlichen Dashboard an. Zusätzlich unterstützt es Firmware-Updates über OpenBLT/XCP Bootloader-Protokoll.

## Features

- **Live CAN-Bus Überwachung**: Echtzeit-Auswertung von CAN-Nachrichten
- **Dashboard Visualisierung**: Browser-basiertes Interface mit Echtzeit-Statusanzeige
- **CAN-Konfiguration per UI**: Interface, Kanal und Baudrate direkt im Browser konfigurieren und verbinden/trennen
- **Firmware-Update via OpenBLT**: `.srec`-Dateien per Drag-and-Drop über XCP/CAN flashen
- **ECU-Presets**: Vordefinierte CAN-ID-Paare für BMS, Charger, HBT, MBT, SOC Display und Display-ECUs
- **CSV Export**: Datenexport mit konfigurierbarem Zeitfenster
- **Responsive Design**: Optimiert für Desktop und Tablets

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

Öffne dann `http://localhost:8052` im Browser und klicke auf **Verbinden**, um den CAN-Adapter zu aktivieren.

## Projektstruktur

```
eauto_dashboard.py          # Hauptprogramm und Dashboard-Layout
├── backend/
│   ├── __init__.py
│   ├── can_bus.py          # CAN-Interface, CanManager, Empfangsthread mit Reconnect
│   └── decoders/
│       └── __init__.py     # Decoder-Registry (DECODERS / MULTI_DECODERS)
├── openblt/
│   ├── __init__.py         # Python-Wrapper für libopenblt
│   └── lib.py              # ctypes-Bindings für libopenblt.dll
└── ui/
    ├── __init__.py
    ├── banners.py           # CAN-Lost-Banner Formatierung
    ├── controls.py          # CAN-Konfigurationsfelder, Zeitfenster, Firmware-Upload-Karte
    └── callbacks/
        ├── __init__.py
        ├── can_banner.py    # CAN-Verbindungsstatus Banner
        ├── can_config.py    # CAN-Adapter verbinden/trennen
        ├── ecu_preset.py    # ECU-Preset Dropdown → CAN-ID-Felder befüllen
        ├── export_csv.py    # CSV-Export Callback
        ├── firmware_upload.py  # Firmware-Upload via OpenBLT
        ├── reset.py         # Datenspeicher zurücksetzen
        └── snapshot.py      # Tick → aktuellen Snapshot in dcc.Store schreiben
```

## Architektur

### Backend

- **`backend/can_bus.py`**: Verwaltet die CAN-Verbindung über `CanManager`. Der Empfangsthread wird per UI-Button gestartet und gestoppt. Reconnect-Logik mit exponentiellem Backoff (3 s → 6 s → 12 s, max. 30 s).
- **`backend/decoders/`**: Modulare Decoder für CAN-Nachrichten. Zwei Registries: `DECODERS` für Single-Value-Decoder (Status/State-Paare) und `MULTI_DECODERS` für Decoder die mehrere Keys zurückgeben.

### Frontend

- **`ui/controls.py`**: Wiederverwendbare UI-Komponenten (CAN-Konfigurationsfelder, Zeitfenster-Steuerung, Firmware-Upload-Karte mit ECU-Presets)
- **`ui/banners.py`**: Banner-Formatierung für CAN-Verbindungsverlust
- **`ui/callbacks/`**: Alle Dash-Callbacks für Benutzerinteraktionen und Datenaktualisierungen

### Datenfluss

```
Browser → "Verbinden"-Button
  ↓
can_config.py → CanManager.start()
  ↓
CAN-Bus → can_bus.py (RX-Thread) → latest (thread-safe dict)
  ↓
Dashboard Interval (500 ms)
  ↓
snapshot.py → Datenspeicherung in dcc.Store
  ↓
Callbacks → UI-Update
```

## Firmware-Update Prozess

1. CAN-Adapter in der Titelleiste verbinden.
2. In den Reiter **Bootloader** wechseln.
3. ECU aus dem Dropdown wählen oder CAN-IDs manuell eingeben.
4. `.srec`-Datei in das Upload-Feld ziehen oder per Klick auswählen.
5. Dashboard trennt den CAN-RX-Thread automatisch, öffnet `libopenblt.dll` und wartet bis zu 30 s auf den Bootloader.
6. Flash-Sequenz (entspricht BootCommander): zuerst alle Segmente löschen (Erase-Pass), dann alle schreiben (Write-Pass).
7. Nach erfolgreichem Flash startet das Gerät via `PROGRAM_RESET` neu; der CAN-RX-Thread wird 3 s später automatisch wieder gestartet.

> **Voraussetzung**: `libopenblt.dll` (und ggf. Peer-DLLs wie `peak_pcanusb.dll`) müssen im `openblt/`-Ordner liegen.

## ECU-Presets

| ECU         | Bootloader RX | Bootloader TX |
|---|---|---|
| BMS         | `0x7E0`       | `0x7E1`       |

## Konfigurierbare Parameter

- **Bootloader RX CAN-ID**: ID, über die das Dashboard Befehle an den Bootloader sendet
- **Bootloader TX CAN-ID**: ID, über die der Bootloader Antworten zurücksendet
- **Time Window**: 1 min, 5 min, 30 min oder All-Time

## Lizenz

Siehe [LICENSE](LICENSE)
