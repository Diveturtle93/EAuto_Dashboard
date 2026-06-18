# EAuto Dashboard — Entwickler-Runbook

## Wann dieses Runbook verwenden

- Dashboard starten oder stoppen
- CAN-Interface verbinden (PCAN, Vector, Kvaser, IXXAT, slcan)
- „CAN connection lost"-Banner diagnostizieren
- Daten exportieren oder Firmware-Update auslösen
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
# Standard: Voreinstellung pcan/PCAN_USBBUS1/500 kbps in der UI
python eauto_dashboard.py

# Eigene Voreinstellung für die UI-Felder
python eauto_dashboard.py pcan    PCAN_USBBUS1  500000
python eauto_dashboard.py vector  0             500000
python eauto_dashboard.py kvaser  0             500000
python eauto_dashboard.py slcan   COM3          500000

# Im Browser öffnen
# http://localhost:8052
```

Die Kommandozeilenargumente befüllen nur die Eingabefelder in der Titelleiste vor. Der CAN-Adapter wird **nicht automatisch verbunden** — erst nach Klick auf **Verbinden** im Browser startet der RX-Thread.

Erfolgreicher Start sieht so aus:

```
============================================================
  EAuto Live Dashboard (Windows)
  Standardwerte: pcan / PCAN_USBBUS1 @ 500000 bps
  CAN-Adapter bitte im Browser verbinden.
  Dashboard: http://localhost:8052
============================================================
```

Nach Klick auf **Verbinden** im Browser:

```
[CAN] Manager started: pcan/PCAN_USBBUS1 @ 500000 bps
[CAN] Connected: interface=pcan, channel=PCAN_USBBUS1, bitrate=500000
```

---

## Dashboard stoppen

Im Terminal `Strg+C` drücken. Der CAN-RX-Thread ist ein Daemon-Thread und beendet sich automatisch.

Alternativ: Im Browser auf **Trennen** klicken, um nur den CAN-Thread zu stoppen ohne den Prozess zu beenden.

---

## CAN-Interface verbinden und trennen

Die CAN-Konfiguration befindet sich in der **Titelleiste** des Dashboards:

1. Interface aus dem Dropdown wählen (pcan, vector, kvaser, slcan, ixxat, …).
2. Kanal und Baudrate einstellen.
3. Auf **Verbinden** klicken — es wird ein synchroner Verbindungstest durchgeführt. Schlägt er fehl, erscheint sofort eine Fehlermeldung.
4. Bei Erfolg wechselt der Button zu **Trennen** und die Konfigurationsfelder werden ausgeblendet.

---

## CAN-Interface-Fehlersuche

### Banner „CAN connection lost" erscheint

Das Banner zeigt sich, wenn länger als 3 Sekunden kein Frame empfangen wurde (in den ersten 5 Sekunden nach dem Verbinden unterdrückt).

**Schritt 1 — Terminal-Ausgabe prüfen.**
```
[CAN] Cannot open pcan/PCAN_USBBUS1: ...  -- retrying in 3 s
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
Standard ist 500 kbps. Wenn das Fahrzeug 250 kbps oder 1 Mbps verwendet, die korrekte Bitrate aus dem Dropdown in der Titelleiste wählen und neu verbinden.

**Schritt 4 — Abschlusswiderstand prüfen.**
Ein CAN-Bus braucht an beiden Enden je 120 Ω. Fehlende Terminierung führt zu sporadischem oder keinem Empfang.

**Schritt 5 — Datenspeicher zurücksetzen.**
Im Dashboard auf **Reset** klicken, um veraltete Zeitstempel zu löschen, ohne den Prozess neu zu starten.

---

## Datenexport

Im Dashboard auf **Export CSV** klicken. Die Datei heißt `EAuto_JJJJMMTT_HHMMSS.csv` und wird über den Browser heruntergeladen.

Die CSV enthält zwei Spalten (`key`, `value`) mit dem aktuellen Snapshot. Bei Zeitreihendaten (Legacy-Format) werden alle Spalten mit Zeitstempeln exportiert.

---

## Firmware-Update (OpenBLT via XCP/CAN)

### Voraussetzung

`libopenblt.dll` (und ggf. Peer-DLLs wie `peak_pcanusb.dll`) müssen im `openblt/`-Ordner liegen. Ohne die DLL meldet das Dashboard beim Upload-Versuch einen Fehler.

### Ablauf

1. CAN-Adapter in der Titelleiste verbinden.
2. In den Reiter **Bootloader** wechseln.
3. ECU aus dem **Steuergerät**-Dropdown wählen — die CAN-IDs werden automatisch eingetragen.
4. `.srec`-Datei per Drag-and-Drop oder Klick hochladen.
5. Dashboard stoppt den CAN-RX-Thread, öffnet `libopenblt` und wartet bis zu 30 s auf den Bootloader.
6. Flash-Sequenz (entspricht BootCommander): zuerst alle Segmente löschen, dann alle schreiben.
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

### Fehlermeldungen

| Meldung | Ursache | Maßnahme |
|---|---|---|
| `libopenblt.dll nicht gefunden` | DLL fehlt im `openblt/`-Ordner | DLL hineinkopieren |
| `Bootloader nach 30 s nicht erreichbar` | Gerät nicht im Bootloader-Modus | Power-Cycle oder Reset während des Wartens |
| `Vektortabelle ungültig` | Firmware für falsche Startadresse kompiliert | Firmware-Datei prüfen |
| `CAN-Bus nicht verbunden` | CAN nicht verbunden | Zuerst **Verbinden** klicken |
| `Flash-Löschung fehlgeschlagen` | Timeout bei `PROGRAM_CLEAR` | Bitrate prüfen; Gerät im Bootloader? |

---

## Neuen CAN-Decoder hinzufügen

### Single-Value-Decoder (Status + State)

1. `backend/decoders/can_0xNNN.py` anlegen:

```python
def decode_0xNNN(data):
    """0xNNN-Payload → (status_code, state_string)."""
    if len(data) < 1:
        return None
    return data[0], "Running" if data[0] == 1 else "Idle"
```

2. In `backend/decoders/__init__.py` registrieren:

```python
from .can_0xNNN import decode_0xNNN

DECODERS[0xNNN] = (decode_0xNNN, "mein_status_code", "mein_state")
```

3. Initialwerte in `latest` in `eauto_dashboard.py` ergänzen:

```python
latest = dict(
    last_rx_ms=0,
    can_adapter_connected=False,
    mein_status_code=None,
    mein_state="Unknown",
)
```

4. Anzeige in einem eigenen Callback oder direkt im Dashboard-Tab-Layout ergänzen.

### Multi-Value-Decoder (mehrere Keys)

```python
# backend/decoders/__init__.py
from .can_0xNNN import decode_0xNNN

MULTI_DECODERS[0xNNN] = decode_0xNNN  # decode_0xNNN(data) → {key: value, ...}
```

---

## Projektstruktur

```
eauto_dashboard.py          Einstiegspunkt, Layout, Callback-Registrierung
backend/
  can_bus.py                CanManager, CAN-RX-Thread, Reconnect-Logik mit Backoff
  decoders/
    __init__.py             Decoder-Registries (DECODERS / MULTI_DECODERS)
openblt/
  __init__.py               Python-Wrapper für libopenblt
  lib.py                    ctypes-Bindings für libopenblt.dll
ui/
  banners.py                Formatierung des CAN-Lost-Banners
  controls.py               CAN-Konfigurationsfelder, Zeitfenster-Steuerung, Firmware-Upload-Karte
  callbacks/
    can_banner.py           CAN-Lost-Banner ein-/ausblenden
    can_config.py           CAN-Adapter verbinden/trennen
    ecu_preset.py           ECU-Dropdown → CAN-ID-Felder befüllen
    export_csv.py           CSV-Download
    firmware_upload.py      Firmware-Flash-Sequenz via libopenblt
    reset.py                Datenspeicher zurücksetzen
    snapshot.py             Tick → aktuellen Snapshot in dcc.Store
```

---

## Eskalation

| Symptom | Maßnahme |
|---|---|
| CAN-Frames empfangen, dekodierte Werte falsch | Decoder in `backend/decoders/` prüfen |
| Banner flackert | `last_rx_ms`-Update in `can_bus.py` prüfen |
| Dashboard lädt nicht | Terminal auf Python-Import-Fehler prüfen |
| Firmware-Upload-Button reagiert nicht | `register_firmware_upload_callback` fehlt in `eauto_dashboard.py` — Import ergänzen und `register_firmware_upload_callback(app, can_manager, latest, lock)` aufrufen |
| libopenblt-Fehler beim Flash | DLL im `openblt/`-Ordner prüfen; bei PCAN auch `peak_pcanusb.dll` prüfen |
