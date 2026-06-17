import base64
import os
import re
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

_CONNECT_TIMEOUT = 30     # seconds to wait for bootloader to become available
_ERASE_CHUNK     = 32768  # 32 KB per PROGRAM_CLEAR call  – matches BootCommander
_WRITE_CHUNK     = 256    # 256 B  per BltSessionWriteData – matches BootCommander


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
    """Execute the OpenBLT firmware update sequence. Returns a Dash component."""
    try:
        import openblt  # lazy import – libopenblt.dll must be present at flash time
    except (OSError, ImportError) as exc:
        return html.Span(
            f"Fehler: libopenblt.dll nicht gefunden – bitte in den openblt-Ordner kopieren. ({exc})",
            style={"color": "#c0392b"},
        )

    openblt.firmware_init(openblt.BLT_FIRMWARE_PARSER_SRECORD)
    try:
        if openblt.firmware_load_from_file(tmp_path, 0) != openblt.BLT_RESULT_OK:
            return html.Span(
                "Fehler: Firmware-Datei konnte nicht geladen werden (kein gültiges S-Record?).",
                style={"color": "#c0392b"},
            )

        seg_count = openblt.firmware_get_segment_count()
        if seg_count == 0:
            return html.Span(
                "Fehler: Keine Firmware-Segmente in der Datei gefunden.",
                style={"color": "#c0392b"},
            )

        # Pre-load all segment data into Python lists before starting the session.
        segments = []
        for i in range(seg_count):
            seg_data, seg_addr, seg_len = openblt.firmware_get_segment(i)
            segments.append((list(seg_data), seg_addr, seg_len))

        # Validate vector table of the first segment (should be at APP_START)
        vec_lines = []
        first_data, first_addr, first_len = segments[0]
        if first_len >= 8:
            sp = (first_data[0] | (first_data[1] << 8) |
                  (first_data[2] << 16) | (first_data[3] << 24))
            rv = (first_data[4] | (first_data[5] << 8) |
                  (first_data[6] << 16) | (first_data[7] << 24))
            sp_ok = 0x20000000 <= sp <= 0x2FFFFFFF
            rv_ok = 0x08000000 <= (rv & ~1) <= 0x0FFFFFFF and bool(rv & 1)
            vec_lines = [
                html.Div(
                    f"  Vektortabelle @ 0x{first_addr:08X}:  "
                    f"SP=0x{sp:08X} {'✓' if sp_ok else '✗ (ungültig!)'}  "
                    f"RV=0x{rv:08X} {'✓' if rv_ok else '✗ (ungültig!)'}",
                    style={
                        "fontFamily": "monospace", "fontSize": "11px",
                        "color": "#27ae60" if (sp_ok and rv_ok) else "#c0392b",
                    },
                )
            ]
            if not (sp_ok and rv_ok):
                return html.Div([
                    html.Span(
                        "Fehler: Vektortabelle der Firmware ist ungültig — "
                        "der Bootloader würde die Applikation nicht starten.",
                        style={"color": "#c0392b", "fontWeight": "600"},
                    ),
                    *vec_lines,
                    html.Div(
                        "Mögliche Ursache: Firmware nicht für die korrekte Startadresse "
                        f"(0x{first_addr:08X}) kompiliert. Flash wird nicht durchgeführt.",
                        style={"fontSize": "11px", "color": "#888", "marginTop": "4px"},
                    ),
                ])

        session_settings = openblt.BltSessionSettingsXcpV10()
        session_settings.timeoutT4 = 60000  # erase timeout 60 s for large flash regions

        transport_settings = openblt.BltTransportSettingsXcpV10Can()
        transport_settings.deviceName    = device_name
        transport_settings.deviceChannel = device_channel
        transport_settings.baudrate      = baudrate
        transport_settings.transmitId    = transmit_id  # host → bootloader
        transport_settings.receiveId     = receive_id   # bootloader → host
        transport_settings.useExtended   = 0
        transport_settings.brsBaudrate   = 0

        # ── Connect: init ONCE, then retry session_start in a tight loop ────────────
        # BootCommander does exactly this – it never calls init/terminate per retry.
        openblt.session_init(
            openblt.BLT_SESSION_XCP_V10, session_settings,
            openblt.BLT_TRANSPORT_XCP_V10_CAN, transport_settings,
        )
        try:
            deadline = time.monotonic() + _CONNECT_TIMEOUT
            connected = False
            while time.monotonic() < deadline:
                if openblt.session_start() == openblt.BLT_RESULT_OK:
                    connected = True
                    break
                time.sleep(0.02)  # 20 ms between attempts – same as BootCommander

            if not connected:
                return html.Span(
                    f"Fehler: Bootloader nach {_CONNECT_TIMEOUT} s nicht erreichbar. "
                    "Bitte Gerät innerhalb des Zeitfensters in den Bootloader-Modus versetzen "
                    "(Reset / Power-Cycle).",
                    style={"color": "#c0392b"},
                )

            try:
                total_bytes = 0
                segment_info = []

                # ── Pass 1: erase ALL segments before writing any ──────────────────
                # Matches BootCommander's sequence: all erases first, then all writes.
                # The OpenBLT bootloader builds its valid-app checksum based on the
                # full programmed address range; interleaving erases with writes causes
                # it to compute the checksum over an incomplete range.
                for seg_data, seg_addr, seg_len in segments:
                    remaining = seg_len
                    addr = seg_addr
                    while remaining > 0:
                        chunk = min(remaining, _ERASE_CHUNK)
                        if openblt.session_clear_memory(addr, chunk) != openblt.BLT_RESULT_OK:
                            return html.Span(
                                f"Fehler: Flash-Löschung fehlgeschlagen (Adresse 0x{addr:08X}).",
                                style={"color": "#c0392b"},
                            )
                        addr      += chunk
                        remaining -= chunk

                # ── Pass 2: write ALL segments ────────────────────────────────────
                for seg_data, seg_addr, seg_len in segments:
                    remaining = seg_len
                    addr      = seg_addr
                    offset    = 0
                    while remaining > 0:
                        chunk = min(remaining, _WRITE_CHUNK)
                        if openblt.session_write_data(
                            addr, chunk, seg_data[offset:offset + chunk]
                        ) != openblt.BLT_RESULT_OK:
                            return html.Span(
                                f"Fehler: Schreiben fehlgeschlagen (Adresse 0x{addr:08X}).",
                                style={"color": "#c0392b"},
                            )
                        addr      += chunk
                        offset    += chunk
                        remaining -= chunk

                    segment_info.append((seg_addr, seg_addr + seg_len - 1, seg_len))
                    total_bytes += seg_len

                seg_lines = [
                    html.Div(
                        f"  Segment {j + 1}: 0x{a0:08X} – 0x{a1:08X}  ({ln} Bytes)",
                        style={"fontFamily": "monospace", "fontSize": "11px", "color": "#555"},
                    )
                    for j, (a0, a1, ln) in enumerate(segment_info)
                ]
                return html.Div([
                    html.Span(
                        f"Firmware erfolgreich übertragen!  "
                        f"Datei: {filename} · {seg_count} Segment(e) · {total_bytes} Bytes",
                        style={"color": "#27ae60", "fontWeight": "600"},
                    ),
                    html.Div(seg_lines, style={"marginTop": "4px"}),
                    *vec_lines,
                    html.Div(
                        "Das Gerät wird via PROGRAM_RESET automatisch neu gestartet. "
                        "Falls die Applikation nicht läuft: Gerät manuell neu starten (Power-Cycle).",
                        style={"fontSize": "11px", "color": "#888", "marginTop": "4px"},
                    ),
                ])

            finally:
                openblt.session_stop()
                # Give the PCAN controller time to actually transmit the PROGRAM_RESET frame
                # (0xCF) before session_terminate() closes the CAN channel and discards its
                # TX buffer.  Without this pause the frame is queued but never sent.
                time.sleep(0.2)

        finally:
            openblt.session_terminate()

    finally:
        openblt.firmware_terminate()


def register_firmware_upload_callback(app, can_manager, latest, lock):
    @app.callback(
        Output("bootloader_status", "children"),
        Output("firmware_upload", "contents"),
        Output("firmware_upload", "filename"),
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
            ), None, None

        try:
            transmit_id = _parse_can_id(rx_id_str)  # host transmits to bootloader RX ID
            receive_id  = _parse_can_id(tx_id_str)  # host receives from bootloader TX ID
        except (ValueError, TypeError):
            return html.Span("Fehler: Ungültige CAN-ID eingegeben.", style={"color": "#c0392b"}), None, None

        if not can_manager.is_running:
            return html.Span(
                "Fehler: CAN-Bus nicht verbunden. Bitte zuerst im Konfigurationsfeld verbinden.",
                style={"color": "#c0392b"},
            ), None, None

        cfg = can_manager.config
        device_name, device_channel = _openblt_device(cfg.interface, cfg.channel)

        if not device_name:
            return html.Span(
                f"Fehler: Interface '{cfg.interface}' wird von OpenBLT nicht unterstützt "
                f"(unterstützt: {', '.join(_INTERFACE_MAP.keys())}).",
                style={"color": "#c0392b"},
            ), None, None

        try:
            _, b64 = contents.split(",", 1)
            file_bytes = base64.b64decode(b64)
        except Exception as exc:
            return html.Span(f"Fehler beim Lesen der Datei: {exc}", style={"color": "#c0392b"}), None, None

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".srec", delete=False) as f:
                tmp_path = f.name
                f.write(file_bytes)

            # OpenBLT needs exclusive access – pause the CAN receive thread.
            # A short delay after stop() ensures the PCAN driver is fully released
            # before libopenblt opens it.
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
            return result, None, None

        except Exception as exc:
            return html.Span(f"Unerwarteter Fehler: {exc}", style={"color": "#c0392b"}), None, None

        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
