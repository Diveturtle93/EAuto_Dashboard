import base64
import os
import re
import tempfile
import threading
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

# Global flash progress state – written by flash thread, read by poll callback
_flash_state = {
    "running":      False,
    "phase":        "idle",   # idle | connecting | erasing | writing | done
    "erase_done":   0,
    "erase_total":  1,
    "write_done":   0,
    "write_total":  1,
    "result":       None,     # Dash component shown when phase == "done"
}


def _set_state(**kwargs):
    _flash_state.update(kwargs)


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
        m = re.search(r"(\d+)$", channel)
        if m:
            device_channel = max(0, int(m.group(1)) - 1)
    else:
        try:
            device_channel = int(channel)
        except (ValueError, TypeError):
            device_channel = 0
    return device_name, device_channel


def _single_bar(label, pct, sub):
    """Render one labeled progress bar row."""
    color = "#2980b9"
    return html.Div(
        style={"marginBottom": "10px"},
        children=[
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "baseline",
                    "marginBottom": "5px",
                },
                children=[
                    html.Span(label, style={"fontSize": "12px", "fontWeight": "700", "color": "#333"}),
                    html.Span(f"{pct:.0f} %", style={"fontSize": "13px", "fontWeight": "700", "color": color}),
                ],
            ),
            html.Div(
                style={"background": "#dde3ea", "borderRadius": "5px", "height": "10px", "overflow": "hidden"},
                children=[
                    html.Div(style={
                        "background": color,
                        "width": f"{pct:.1f}%",
                        "height": "100%",
                        "borderRadius": "5px",
                        "transition": "width 0.2s ease",
                    })
                ],
            ),
            html.Div(sub, style={"fontSize": "11px", "color": "#888", "marginTop": "3px"}),
        ],
    )


def _progress_bar_ui():
    """Build progress bar component from current _flash_state."""
    phase = _flash_state["phase"]
    if phase not in ("connecting", "erasing", "writing"):
        return html.Div()

    if phase == "connecting":
        erase_pct = 0.0
        erase_sub = "–"
        write_pct = 0.0
        write_sub = "–"
    elif phase == "erasing":
        done  = _flash_state["erase_done"]
        total = max(_flash_state["erase_total"], 1)
        erase_pct = (done / total) * 100.0
        erase_sub = f"{done:,} / {total:,} Bytes"
        write_pct = 0.0
        write_sub = "–"
    else:  # writing
        erase_pct = 100.0
        erase_sub = f"{_flash_state['erase_total']:,} Bytes"
        done  = _flash_state["write_done"]
        total = max(_flash_state["write_total"], 1)
        write_pct = (done / total) * 100.0
        write_sub = f"{done:,} / {total:,} Bytes"

    status_label = {
        "connecting": "Verbinde mit Bootloader …",
        "erasing":    "Lösche Flash …",
        "writing":    "Schreibe Firmware …",
    }[phase]

    return html.Div(
        style={
            "background": "#f7f9fc",
            "border": "1px solid #dfe3ea",
            "borderRadius": "8px",
            "padding": "12px 14px",
            "marginTop": "10px",
        },
        children=[
            html.Div(
                status_label,
                style={"fontSize": "11px", "fontWeight": "700", "color": "#888",
                       "textTransform": "uppercase", "letterSpacing": "0.06em", "marginBottom": "10px"},
            ),
            _single_bar("Flash löschen", erase_pct, erase_sub),
            _single_bar("Firmware schreiben", write_pct, write_sub),
        ],
    )


def _run_flash(tmp_path, filename, device_name, device_channel, baudrate, transmit_id, receive_id):
    """Execute the OpenBLT firmware update sequence. Returns a Dash component. Updates _flash_state for progress."""
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

        total_bytes = sum(seg_len for _, _, seg_len in segments)

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
                segment_info = []

                # ── Pass 1: erase ALL segments before writing any ──────────────────
                # Matches BootCommander's sequence: all erases first, then all writes.
                # The OpenBLT bootloader builds its valid-app checksum based on the
                # full programmed address range; interleaving erases with writes causes
                # it to compute the checksum over an incomplete range.
                erase_done = 0
                _set_state(phase="erasing", erase_done=0, erase_total=total_bytes)
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
                        addr       += chunk
                        remaining  -= chunk
                        erase_done += chunk
                        _set_state(erase_done=erase_done)

                # ── Pass 2: write ALL segments ────────────────────────────────────
                write_done = 0
                _set_state(phase="writing", write_done=0, write_total=total_bytes)
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
                        addr       += chunk
                        offset     += chunk
                        remaining  -= chunk
                        write_done += chunk
                        _set_state(write_done=write_done)
                    segment_info.append((seg_addr, seg_addr + seg_len - 1, seg_len))

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


def _flash_thread(tmp_path, filename, can_manager, cfg, latest, lock,
                  device_name, device_channel, transmit_id, receive_id):
    """Background thread: runs flash, restores CAN bus, then marks state as done."""
    try:
        result = _run_flash(
            tmp_path, filename,
            device_name, device_channel,
            cfg.bitrate, transmit_id, receive_id,
        )
    except Exception as exc:
        result = html.Span(f"Unerwarteter Fehler: {exc}", style={"color": "#c0392b"})
    finally:
        # Give the target time to store the checksum, reset, and start the app.
        time.sleep(3.0)
        try:
            can_manager.start(cfg, latest, lock)
        except Exception:
            pass
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    _set_state(running=False, phase="done", result=result)


def register_firmware_upload_callback(app, can_manager, latest, lock):

    @app.callback(
        Output("bootloader_status", "children"),
        Output("flash_poll", "disabled"),
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
            ), True, None, None

        if _flash_state["running"]:
            return html.Span(
                "Flash-Vorgang läuft bereits – bitte warten.",
                style={"color": "#e67e22"},
            ), True, None, None

        try:
            transmit_id = _parse_can_id(rx_id_str)  # host transmits to bootloader RX ID
            receive_id  = _parse_can_id(tx_id_str)  # host receives from bootloader TX ID
        except (ValueError, TypeError):
            return html.Span("Fehler: Ungültige CAN-ID eingegeben.", style={"color": "#c0392b"}), True, None, None

        if not can_manager.is_running:
            return html.Span(
                "Fehler: CAN-Bus nicht verbunden. Bitte zuerst im Konfigurationsfeld verbinden.",
                style={"color": "#c0392b"},
            ), True, None, None

        cfg = can_manager.config
        device_name, device_channel = _openblt_device(cfg.interface, cfg.channel)

        if not device_name:
            return html.Span(
                f"Fehler: Interface '{cfg.interface}' wird von OpenBLT nicht unterstützt "
                f"(unterstützt: {', '.join(_INTERFACE_MAP.keys())}).",
                style={"color": "#c0392b"},
            ), True, None, None

        try:
            _, b64 = contents.split(",", 1)
            file_bytes = base64.b64decode(b64)
        except Exception as exc:
            return html.Span(f"Fehler beim Lesen der Datei: {exc}", style={"color": "#c0392b"}), True, None, None

        try:
            with tempfile.NamedTemporaryFile(suffix=".srec", delete=False) as f:
                tmp_path = f.name
                f.write(file_bytes)
        except Exception as exc:
            return html.Span(f"Fehler beim Speichern der Datei: {exc}", style={"color": "#c0392b"}), True, None, None

        # All checks passed – initialise state and hand off to background thread
        _set_state(
            running=True, phase="connecting", result=None,
            erase_done=0, erase_total=1, write_done=0, write_total=1,
        )

        # OpenBLT needs exclusive access – pause the CAN receive thread first.
        can_manager.stop()
        time.sleep(0.5)

        threading.Thread(
            target=_flash_thread,
            args=(tmp_path, filename, can_manager, cfg, latest, lock,
                  device_name, device_channel, transmit_id, receive_id),
            daemon=True,
        ).start()

        # Clear previous error text; enable poll interval
        return "", False, None, None

    @app.callback(
        Output("flash_progress_area", "children"),
        Output("flash_poll", "disabled", allow_duplicate=True),
        Input("flash_poll", "n_intervals"),
        prevent_initial_call=True,
    )
    def _poll_flash_progress(_):
        phase = _flash_state["phase"]
        if phase == "idle":
            raise PreventUpdate
        if phase == "done":
            return _flash_state["result"], True
        return _progress_bar_ui(), False
