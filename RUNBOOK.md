# EAuto Dashboard — Entwickler-Runbook

## Wann dieses Runbook verwenden

- Dashboard starten oder stoppen
- CAN-Interface verbinden (PCAN, Vector, Kvaser, slcan)
- „CAN connection lost"-Banner diagnostizieren
- Daten exportieren oder Firmware-Update auslösen
- Setup an einen anderen Entwickler übergeben

---

## Voraussetzungen

| Anforderung | Details |
|---|---|
| Python | 3.10 oder neuer |
| Abhängigkeiten | `pip install dash plotly python-can` |
| CAN-Adapter | PCAN-USB, Vector, Kvaser oder slcan-kompatibler Adapter |
| Treiber | Herstellertreiber vor dem Start installieren |
| Betriebssystem | Windows (primäres Ziel); Linux funktioniert mit `socketcan` |

Setup prüfen:

```bash
python -c "import can; print(can.__version__)"
python -c "import dash; print(dash.__version__)"
```

---

## Dashboard starten

```bash
# Standard: PCAN-Adapter auf PCAN_USBBUS1 mit 500 kbps
python eauto_dashboard.py

# Eigener Adapter
python eauto_dashboard.py pcan    PCAN_USBBUS1  500000
python eauto_dashboard.py vector  0             500000
python eauto_dashboard.py kvaser  0             500000
python eauto_dashboard.py slcan   COM3          500000

# Im Browser öffnen
# http://localhost:8052
```

Das Dashboard ist nur unter `127.0.0.1` erreichbar — kein Zugriff aus dem Netzwerk.

Erfolgreicher Start sieht so aus:

```
============================================================
  EAuto Live Dashboard (Windows)
  with Status Monitor
  CAN: pcan / PCAN_USBBUS1 @ 500000 bps
  Dashboard: http://localhost:8052
============================================================
[CAN] Connected: interface=pcan, channel=PCAN_USBBUS1, bitrate=500000
```

---

## Dashboard stoppen

Im Terminal `Strg+C` drücken. Der CAN-RX-Thread ist ein Daemon-Thread und beendet sich automatisch.

---

## CAN-Interface-Fehlersuche

### Banner „CAN connection lost" erscheint

Das Banner zeigt sich, wenn länger als 3 Sekunden kein Frame empfangen wurde (in den ersten 5 Sekunden nach dem Start unterdrückt).

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
Standard ist 500 kbps. Wenn das Fahrzeug 250 kbps oder 1 Mbps verwendet, den korrekten Wert als drittes Argument übergeben.

**Schritt 4 — Abschlusswiderstand prüfen.**
Ein CAN-Bus braucht an beiden Enden je 120 Ω. Fehlende Terminierung führt zu sporadischem oder keinem Empfang.

**Schritt 5 — Datenspeicher zurücksetzen.**
Im Dashboard auf **Reset** klicken, um veraltete Zeitstempel zu löschen, ohne den Prozess neu zu starten.

---

## Datenexport

Im Dashboard auf **Export CSV** klicken. Die Datei heißt `EAuto_JJJJMMTT_HHMMSS.csv` und wird über den Browser heruntergeladen.

Die CSV enthält zwei Spalten (`key`, `value`) mit dem aktuellen Snapshot. Bei Zeitreihendaten (Legacy-Format) werden alle Spalten mit Zeitstempeln exportiert.

---

## Neuen CAN-Decoder hinzufügen

1. `backend/decoders/can_0xNNN.py` anlegen:

```python
from .common import decode_status_state

def decode_0xNNN(data):
    """0xNNN-Payload in (status, state) dekodieren."""
    return decode_status_state(data, min_len=1)
```

2. In `backend/decoders/__init__.py` registrieren:

```python
from .can_0xNNN import decode_0xNNN

DECODERS = {
    ...
    0xNNN: (decode_0xNNN, "mein_status_code", "mein_state"),
}
```

3. Initialwerte in `latest` in `eauto_dashboard.py` ergänzen:

```python
latest = dict(
    ...
    mein_status_code=None,
    mein_state="Unknown",
)
```

4. Anzeige in `ui/callbacks/status.py` — neue Felder zur `items`-Liste in `_status()` hinzufügen.

---

## Firmware-Update (nur UI — noch kein Backend)

Die Firmware-Update-Karte nimmt eine Datei entgegen und zeigt drei CAN-ID-Felder:

| Feld | Standard | Zweck |
|---|---|---|
| Bootloader RX CAN-ID | `0x66E` | ID, auf der der Bootloader lauscht |
| Bootloader TX CAN-ID | `0x7EE` | ID, auf der der Bootloader antwortet |
| Programmstartadresse | `0x08003000` | Flash-Startadresse |

Der Upload-Callback ist noch nicht implementiert. Die Flashlogik muss als neuer Callback in `ui/callbacks/` ergänzt und in `eauto_dashboard.py` registriert werden.

---

## Projektstruktur

```
eauto_dashboard.py          Einstiegspunkt, Layout, Callback-Registrierung
backend/
  can_bus.py                CAN-RX-Thread, Reconnect-Logik, Backoff
  decoders/
    __init__.py             Decoder-Registry (CAN-ID → Keys-Zuordnung)
    common.py               Gemeinsame decode_status_state()-Hilfsfunktion
    can_0x505.py            BMS-Decoder (0x505)
    can_0x560.py            Motor-Decoder (0x560)
ui/
  banners.py                Formatierung des CAN-Lost-Banners
  controls.py               Zeitfenster-Steuerung, Firmware-Upload-Karte
  callbacks/
    snapshot.py             Tick → aktueller Snapshot in dcc.Store
    status.py               BMS- und Motorstatus-Felder anzeigen
    can_banner.py           CAN-Lost-Banner ein-/ausblenden
    export_csv.py           CSV-Download
    reset.py                Datenspeicher zurücksetzen
```

---

## Eskalation

| Symptom | Maßnahme |
|---|---|
| CAN-Frames empfangen, dekodierte Werte falsch | Decoder in `backend/decoders/` prüfen |
| Banner flackert | `last_rx_ms`-Update in `can_bus.py` prüfen |
| Dashboard lädt nicht | Terminal auf Python-Import-Fehler prüfen |
| Firmware-Update reagiert nicht | Callback noch nicht implementiert — siehe Abschnitt oben |
