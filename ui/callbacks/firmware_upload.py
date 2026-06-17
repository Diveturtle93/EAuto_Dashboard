import base64
import os
import re
import subprocess
import tempfile
import time

from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate

# Maps python-can interface names to OpenBLT device names (Windows)
_INTERFACE_MAP = {
    "pcan":   "peak_pcanusb",
    "kvaser": "kvaser_canlib",
    "vector": "vector_xldriver",
    "ixxat":  "ixxat_vcidriver",
    "slcan":  "lawicel_canusb",
}

# Look for BootCommander.exe in the openblt/ directory (next to libopenblt.dll)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_BOOTCOMMANDER_PATHS = [
    os.path.join(_PROJECT_ROOT, "openblt", "BootCommander.exe"),
    os.path.join(_PROJECT_ROOT, "BootCommander.exe"),
]

_FLASH_TIMEOUT = 180  # seconds – subprocess timeout for the entire flash operation


def _find_bootcommander():
    for path in _BOOTCOMMANDER_PATHS:
        if os.path.isfile(path):
            return path
    return None


def _parse_can_id(value):
    """Parse a hex (0x...) or decimal string into an integer CAN ID."""
    s = (value or "").strip()
    if s.lower().startswith("0x"):
        return int(s, 16)
    return int(s, 0)


def _openblt_device(interface, channel):
    """Return (device_name, device_channel) for the given python-can interface/channel."""
    device_name = _INTERFACE_MAP.get(interface.lower(), "")
    device_channel = 0
    if interface.lower() == "pcan":
        # PCAN_USBBUS1 → channel 0, PCAN_USBBUS2 → channel 1, …
        m = re.search(r"(\d+)$", channel)
        if m:
            device_channel = max(0, int(m.group(1)) - 1)
    else:
        try:
            device_channel = int(channel)
        except (ValueError, TypeError):
            device_channel = 0
    return device_name, device_channel


def _run_flash(tmp_path, filename, device_name, device_channel, baudrate, transmit_id, receive_id):
    """Flash firmware via BootCommander subprocess. Returns a Dash component."""
    bootcommander = _find_bootcommander()
    if bootcommander is None:
        searched = ", ".join(_BOOTCOMMANDER_PATHS)
        return html.Span(
            f"Fehler: BootCommander.exe nicht gefunden. "
            f"Bitte in den openblt/-Ordner kopieren. (Gesucht in: {searched})",
            style={"color": "#c0392b"},
        )

    cmd = [
        bootcommander,
        "-s=xcp",
        "-t=xcp_can",
        f"-d={device_name}",
        f"-c={device_channel}",
        f"-b={baudrate}",
        f"-tid={transmit_id:x}",
        f"-rid={receive_id:x}",
        "-t4=60000",   # erase timeout 60 s
        "-t3=10000",   # program-start timeout 10 s
        tmp_path,
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_FLASH_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return html.Span(
            f"Timeout: Flashvorgang nach {_FLASH_TIMEOUT} s abgebrochen. "
            "Bitte Gerät neu starten und erneut versuchen.",
            style={"color": "#c0392b"},
        )
    except Exception as exc:
        return html.Span(
            f"Fehler beim Starten von BootCommander: {exc}",
            style={"color": "#c0392b"},
        )

    output = (proc.stdout or "") + (proc.stderr or "")
    output_lines = [ln.strip() for ln in output.splitlines() if ln.strip()]

    if proc.returncode == 0:
        return html.Div([
            html.Span(
                f"Firmware erfolgreich übertragen!  Datei: {filename}",
                style={"color": "#27ae60", "fontWeight": "600"},
            ),
            html.Div(
                [
                    html.Div(ln, style={"fontFamily": "monospace", "fontSize": "11px", "color": "#555"})
                    for ln in output_lines[-12:]
                ],
                style={"marginTop": "4px"},
            ),
            html.Div(
                "Das Gerät wird via PROGRAM_RESET automatisch neu gestartet.",
                style={"fontSize": "11px", "color": "#888", "marginTop": "4px"},
            ),
        ])

    return html.Div([
        html.Span(
            "Flash fehlgeschlagen.",
            style={"color": "#c0392b", "fontWeight": "600"},
        ),
        html.Div(
            [
                html.Div(ln, style={"fontFamily": "monospace", "fontSize": "11px", "color": "#c0392b"})
                for ln in output_lines[-15:]
            ],
            style={"marginTop": "4px"},
        ),
    ])


def register_firmware_upload_callback(app, can_manager, latest, lock):
    @app.callback(
        Output("bootloader_status", "children"),
        Input("firmware_upload", "contents"),
        State("firmware_upload", "filename"),
        State("bootloader_rx_id", "value"),
        State("bootloader_tx_id", "value"),
        prevent_initial_call=True,
    )
    def _flash_firmware(contents, filename, rx_id_str, tx_id_str):
        if contents is None:
            return html.Span(
                "Bitte zuerst eine Firmware-Datei auswählen.",
                style={"color": "#e67e22"},
            )

        try:
            transmit_id = _parse_can_id(rx_id_str)  # host transmits to bootloader RX ID
            receive_id  = _parse_can_id(tx_id_str)  # host receives from bootloader TX ID
        except (ValueError, TypeError):
            return html.Span("Fehler: Ungültige CAN-ID eingegeben.", style={"color": "#c0392b"})

        if not can_manager.is_running:
            return html.Span(
                "Fehler: CAN-Bus nicht verbunden. Bitte zuerst im Konfigurationsfeld verbinden.",
                style={"color": "#c0392b"},
            )

        cfg = can_manager.config
        device_name, device_channel = _openblt_device(cfg.interface, cfg.channel)

        if not device_name:
            return html.Span(
                f"Fehler: Interface '{cfg.interface}' wird von OpenBLT nicht unterstützt "
                f"(unterstützt: {', '.join(_INTERFACE_MAP.keys())}).",
                style={"color": "#c0392b"},
            )

        try:
            _, b64 = contents.split(",", 1)
            file_bytes = base64.b64decode(b64)
        except Exception as exc:
            return html.Span(f"Fehler beim Lesen der Datei: {exc}", style={"color": "#c0392b"})

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".srec", delete=False) as f:
                tmp_path = f.name
                f.write(file_bytes)

            # BootCommander needs exclusive access to the PCAN adapter.
            # Stop the CAN receive thread and wait for the driver to be released.
            can_manager.stop()
            time.sleep(0.5)
            try:
                result = _run_flash(
                    tmp_path, filename,
                    device_name, device_channel,
                    cfg.bitrate, transmit_id, receive_id,
                )
            finally:
                # Give the target time to store the checksum, reset, and start the app.
                time.sleep(3.0)
                can_manager.start(cfg, latest, lock)
            return result

        except Exception as exc:
            return html.Span(f"Unerwarteter Fehler: {exc}", style={"color": "#c0392b"})

        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
