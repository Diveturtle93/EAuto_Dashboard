#-----------------------------------------------------------------------
# Titel		:	firmware_upload.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	17.06.2026
# Version	:	1.0
# Autor		:	Diveturtle93
# Projekt	:	EAuto_Dashboard
# Quelle	:
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------
import base64
import os
import re
import tempfile
import threading
import time
#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_FIRMWARE_UPLOAD							= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
FIRMWARE_UPLOAD_MAJOR							= 1
FIRMWARE_UPLOAD_MINOR							= 0
FIRMWARE_UPLOAD_PATCH							= 0
FIRMWARE_UPLOAD_DEV								= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
# Zuordnung python-can Interface -> OpenBLT Geraetename (Windows)
_INTERFACE_MAP									= {
	"pcan": "peak_pcanusb",
	"kvaser": "kvaser_canlib",
	"vector": "vector_xldriver",
	"ixxat": "ixxat_vcidriver",
	"slcan": "lawicel_canusb",
}

_CONNECT_TIMEOUT								= 30						# Wartezeit auf den Bootloader in s
_ERASE_CHUNK									= 32768						# 32 KB pro PROGRAM_CLEAR, wie BootCommander
_WRITE_CHUNK									= 256						# 256 B pro BltSessionWriteData, wie BootCommander
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------
# Globaler Fortschritt des Flash-Vorgangs, geschrieben vom Flash-Thread, gelesen vom Poll-Callback
_flashState = {
	"running": False,
	"phase": "idle",														# idle | connecting | erasing | writing | done
	"eraseDone": 0,
	"eraseTotal": 1,
	"writeDone": 0,
	"writeTotal": 1,
	"result": None,															# Dash-Komponente, wird bei phase == "done" angezeigt
}
#-----------------------------------------------------------------------

# Felder des Flash-Fortschritts setzen
#-----------------------------------------------------------------------
def _setState (**kwargs):
	_flashState.update(kwargs)
#-----------------------------------------------------------------------

# Hex- (0x...) oder Dezimal-String in eine CAN-ID wandeln
#-----------------------------------------------------------------------
def _parseCanId (value):
	s = (value or "").strip()
	if s.lower().startswith("0x"):
		return int(s, 16)

	return int(s, 0)
#-----------------------------------------------------------------------

# OpenBLT Geraetename und -kanal zu python-can Interface und Kanal ermitteln
# Rueckgabe: (deviceName, deviceChannel)
#-----------------------------------------------------------------------
def _openbltDevice (interface, channel):
	deviceName = _INTERFACE_MAP.get(interface.lower(), "")
	deviceChannel = 0

	# PCAN: Kanalnummer aus "PCAN_USBBUSx" lesen, OpenBLT zaehlt ab 0
	if interface.lower() == "pcan":
		m = re.search(r"(\d+)$", channel)
		if m:
			deviceChannel = max(0, int(m.group(1)) - 1)
	# Andere Interfaces: Kanal ist bereits eine Zahl
	else:
		try:
			deviceChannel = int(channel)
		except (ValueError, TypeError):
			deviceChannel = 0

	return deviceName, deviceChannel
#-----------------------------------------------------------------------

# Eine beschriftete Fortschrittsbalken-Zeile aufbauen
#-----------------------------------------------------------------------
def _singleBar (label, pct, sub):
	color = "var(--accent)"
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
					html.Span(label, style={"fontSize": "12px", "fontWeight": "700", "color": "var(--text)"}),
					html.Span(f"{pct:.0f} %", style={"fontSize": "13px", "fontWeight": "700", "color": color}),
				],
			),
			html.Div(
				style={"background": "var(--border)", "borderRadius": "5px", "height": "10px", "overflow": "hidden"},
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
			html.Div(sub, style={"fontSize": "11px", "color": "var(--text-muted)", "marginTop": "3px"}),
		],
	)
#-----------------------------------------------------------------------

# Fortschrittsanzeige aus dem aktuellen _flashState aufbauen
#-----------------------------------------------------------------------
def _progressBarUi ():
	phase = _flashState["phase"]
	if phase not in ("connecting", "erasing", "writing"):
		return html.Div()

	# Werte der beiden Balken je nach Phase
	if phase == "connecting":
		erasePct = 0.0
		eraseSub = "\u2013"
		writePct = 0.0
		writeSub = "\u2013"
	elif phase == "erasing":
		done = _flashState["eraseDone"]
		total = max(_flashState["eraseTotal"], 1)
		erasePct = (done / total) * 100.0
		eraseSub = f"{done:,} / {total:,} Bytes"
		writePct = 0.0
		writeSub = "\u2013"
	# writing
	else:
		erasePct = 100.0
		eraseSub = f"{_flashState['eraseTotal']:,} Bytes"
		done = _flashState["writeDone"]
		total = max(_flashState["writeTotal"], 1)
		writePct = (done / total) * 100.0
		writeSub = f"{done:,} / {total:,} Bytes"

	statusLabel = {
		"connecting": "Verbinde mit Bootloader \u2026",
		"erasing": "L\u00f6sche Flash \u2026",
		"writing": "Schreibe Firmware \u2026",
	}[phase]

	return html.Div(
		style={
			"background": "var(--bg-card)",
			"border": "1px solid var(--border)",
			"borderRadius": "8px",
			"padding": "12px 14px",
			"marginTop": "10px",
		},
		children=[
			html.Div(
				statusLabel,
				style={
					"fontSize": "11px", "fontWeight": "700", "color": "var(--text-muted)",
					"textTransform": "uppercase", "letterSpacing": "0.06em", "marginBottom": "10px",
				},
			),
			_singleBar("Flash l\u00f6schen", erasePct, eraseSub),
			_singleBar("Firmware schreiben", writePct, writeSub),
		],
	)
#-----------------------------------------------------------------------

# Firmware-Update ueber OpenBLT ausfuehren und _flashState fortschreiben
# Rueckgabe: Dash-Komponente mit dem Ergebnis
#-----------------------------------------------------------------------
def _runFlash (tmpPath, filename, deviceName, deviceChannel, baudrate, transmitId, receiveId):
	# Verzoegerter Import, libopenblt.dll wird erst beim Flashen benoetigt
	try:
		import openblt
	except (OSError, ImportError) as exc:
		return html.Span(
			f"Fehler: libopenblt.dll nicht gefunden \u2013 bitte in den openblt-Ordner kopieren. ({exc})",
			style={"color": "var(--err-strong)"},
		)

	openblt.firmware_init(openblt.BLT_FIRMWARE_PARSER_SRECORD)
	try:
		if openblt.firmware_load_from_file(tmpPath, 0) != openblt.BLT_RESULT_OK:
			return html.Span(
				"Fehler: Firmware-Datei konnte nicht geladen werden (kein g\u00fcltiges S-Record?).",
				style={"color": "var(--err-strong)"},
			)

		segCount = openblt.firmware_get_segment_count()
		if segCount == 0:
			return html.Span(
				"Fehler: Keine Firmware-Segmente in der Datei gefunden.",
				style={"color": "var(--err-strong)"},
			)

		# Alle Segmentdaten vor dem Start der Session in Python-Listen laden
		segments = []
		for i in range(segCount):
			segData, segAddr, segLen = openblt.firmware_get_segment(i)
			segments.append((list(segData), segAddr, segLen))

		# Vektortabelle des ersten Segments pruefen (sollte auf APP_START liegen)
		vecLines = []
		firstData, firstAddr, firstLen = segments[0]
		if firstLen >= 8:
			sp = firstData[0] | (firstData[1] << 8) | (firstData[2] << 16) | (firstData[3] << 24)
			rv = firstData[4] | (firstData[5] << 8) | (firstData[6] << 16) | (firstData[7] << 24)
			spOk = 0x20000000 <= sp <= 0x2FFFFFFF
			rvOk = 0x08000000 <= (rv & ~1) <= 0x0FFFFFFF and bool(rv & 1)
			spMark = "\u2713" if spOk else "\u2717 (ung\u00fcltig!)"
			rvMark = "\u2713" if rvOk else "\u2717 (ung\u00fcltig!)"
			vecLines = [
				html.Div(
					f"  Vektortabelle @ 0x{firstAddr:08X}:  "
					f"SP=0x{sp:08X} {spMark}  "
					f"RV=0x{rv:08X} {rvMark}",
					style={
						"fontFamily": "monospace", "fontSize": "11px",
						"color": "var(--ok-alt)" if (spOk and rvOk) else "var(--err-strong)",
					},
				)
			]

			# Ungueltige Vektortabelle, nicht flashen
			if not (spOk and rvOk):
				return html.Div([
					html.Span(
						"Fehler: Vektortabelle der Firmware ist ung\u00fcltig \u2014 "
						"der Bootloader w\u00fcrde die Applikation nicht starten.",
						style={"color": "var(--err-strong)", "fontWeight": "600"},
					),
					*vecLines,
					html.Div(
						"M\u00f6gliche Ursache: Firmware nicht f\u00fcr die korrekte Startadresse "
						f"(0x{firstAddr:08X}) kompiliert. Flash wird nicht durchgef\u00fchrt.",
						style={"fontSize": "11px", "color": "var(--text-muted)", "marginTop": "4px"},
					),
				])

		totalBytes = sum(segLen for _, _, segLen in segments)

		# Session- und Transport-Einstellungen
		sessionSettings = openblt.BltSessionSettingsXcpV10()
		sessionSettings.timeoutT4 = 60000									# Erase-Timeout 60 s fuer grosse Flash-Bereiche

		transportSettings = openblt.BltTransportSettingsXcpV10Can()
		transportSettings.deviceName = deviceName
		transportSettings.deviceChannel = deviceChannel
		transportSettings.baudrate = baudrate
		transportSettings.transmitId = transmitId							# Host -> Bootloader
		transportSettings.receiveId = receiveId								# Bootloader -> Host
		transportSettings.useExtended = 0
		transportSettings.brsBaudrate = 0

		# Verbinden: init EINMAL, dann session_start in enger Schleife wiederholen
		# BootCommander macht genau das, init/terminate werden nie pro Versuch aufgerufen.
		openblt.session_init(
			openblt.BLT_SESSION_XCP_V10, sessionSettings,
			openblt.BLT_TRANSPORT_XCP_V10_CAN, transportSettings,
		)
		try:
			deadline = time.monotonic() + _CONNECT_TIMEOUT
			connected = False
			while time.monotonic() < deadline:
				if openblt.session_start() == openblt.BLT_RESULT_OK:
					connected = True
					break
				time.sleep(0.02)											# 20 ms zwischen den Versuchen, wie BootCommander

			if not connected:
				return html.Span(
					f"Fehler: Bootloader nach {_CONNECT_TIMEOUT} s nicht erreichbar. "
					"Bitte Ger\u00e4t innerhalb des Zeitfensters in den Bootloader-Modus versetzen "
					"(Reset / Power-Cycle).",
					style={"color": "var(--err-strong)"},
				)

			try:
				segmentInfo = []

				# Durchlauf 1: ALLE Segmente loeschen, bevor irgendetwas geschrieben wird
				# Entspricht der Reihenfolge von BootCommander: erst alle Erases, dann alle Writes.
				# Der OpenBLT-Bootloader bildet die Valid-App-Checksumme ueber den gesamten
				# programmierten Adressbereich; abwechselndes Loeschen und Schreiben fuehrt
				# dazu, dass die Checksumme ueber einen unvollstaendigen Bereich berechnet wird.
				eraseDone = 0
				_setState(phase="erasing", eraseDone=0, eraseTotal=totalBytes)
				for segData, segAddr, segLen in segments:
					remaining = segLen
					addr = segAddr
					while remaining > 0:
						chunk = min(remaining, _ERASE_CHUNK)
						if openblt.session_clear_memory(addr, chunk) != openblt.BLT_RESULT_OK:
							return html.Span(
								f"Fehler: Flash-L\u00f6schung fehlgeschlagen (Adresse 0x{addr:08X}).",
								style={"color": "var(--err-strong)"},
							)
						addr += chunk
						remaining -= chunk
						eraseDone += chunk
						_setState(eraseDone=eraseDone)

				# Durchlauf 2: ALLE Segmente schreiben
				writeDone = 0
				_setState(phase="writing", writeDone=0, writeTotal=totalBytes)
				for segData, segAddr, segLen in segments:
					remaining = segLen
					addr = segAddr
					offset = 0
					while remaining > 0:
						chunk = min(remaining, _WRITE_CHUNK)
						if openblt.session_write_data(addr, chunk, segData[offset:offset + chunk]) != openblt.BLT_RESULT_OK:
							return html.Span(
								f"Fehler: Schreiben fehlgeschlagen (Adresse 0x{addr:08X}).",
								style={"color": "var(--err-strong)"},
							)
						addr += chunk
						offset += chunk
						remaining -= chunk
						writeDone += chunk
						_setState(writeDone=writeDone)
					segmentInfo.append((segAddr, segAddr + segLen - 1, segLen))

				# Erfolgsmeldung mit Segmentuebersicht
				segLines = [
					html.Div(
						f"  Segment {j + 1}: 0x{a0:08X} \u2013 0x{a1:08X}  ({ln} Bytes)",
						style={"fontFamily": "monospace", "fontSize": "11px", "color": "var(--text-muted)"},
					)
					for j, (a0, a1, ln) in enumerate(segmentInfo)
				]
				return html.Div([
					html.Span(
						f"Firmware erfolgreich \u00fcbertragen!  "
						f"Datei: {filename} \u00b7 {segCount} Segment(e) \u00b7 {totalBytes} Bytes",
						style={"color": "var(--ok-alt)", "fontWeight": "600"},
					),
					html.Div(segLines, style={"marginTop": "4px"}),
					*vecLines,
					html.Div(
						"Das Ger\u00e4t wird via PROGRAM_RESET automatisch neu gestartet. "
						"Falls die Applikation nicht l\u00e4uft: Ger\u00e4t manuell neu starten (Power-Cycle).",
						style={"fontSize": "11px", "color": "var(--text-muted)", "marginTop": "4px"},
					),
				])

			finally:
				openblt.session_stop()
				# Dem PCAN-Controller Zeit geben, den PROGRAM_RESET-Frame (0xCF) wirklich zu
				# senden, bevor session_terminate() den CAN-Kanal schliesst und den TX-Puffer
				# verwirft. Ohne diese Pause wird der Frame eingereiht, aber nie gesendet.
				time.sleep(0.2)

		finally:
			openblt.session_terminate()

	finally:
		openblt.firmware_terminate()
#-----------------------------------------------------------------------

# Hintergrund-Thread: Flash ausfuehren, CAN-Bus wiederherstellen, Zustand auf done setzen
#-----------------------------------------------------------------------
def _flashThread (tmpPath, filename, canManager, cfg, latest, lock, deviceName, deviceChannel, transmitId, receiveId):
	try:
		result = _runFlash(
			tmpPath, filename,
			deviceName, deviceChannel,
			cfg.bitrate, transmitId, receiveId,
		)
	except Exception as exc:
		result = html.Span(f"Unerwarteter Fehler: {exc}", style={"color": "var(--err-strong)"})
	finally:
		# Dem Steuergeraet Zeit geben, die Checksumme zu speichern, neu zu starten und die Applikation zu starten
		time.sleep(3.0)
		try:
			canManager.start(cfg, latest, lock)
		except Exception:
			pass
		try:
			os.unlink(tmpPath)
		except OSError:
			pass

	_setState(running=False, phase="done", result=result)
#-----------------------------------------------------------------------

# Callbacks fuer Firmware-Upload und Fortschrittsanzeige registrieren
#-----------------------------------------------------------------------
def registerFirmwareUploadCallback (app, canManager, latest, lock):
	# Hochgeladene Firmware pruefen und Flash-Thread starten
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
	def _flashFirmware (contents, filename, rxIdStr, txIdStr):
		if contents is None:
			return html.Span(
				"Bitte zuerst eine Firmware-Datei ausw\u00e4hlen.",
				style={"color": "var(--accent)"},
			), True, None, None

		if _flashState["running"]:
			return html.Span(
				"Flash-Vorgang l\u00e4uft bereits \u2013 bitte warten.",
				style={"color": "var(--accent)"},
			), True, None, None

		# CAN-IDs lesen
		try:
			transmitId = _parseCanId(rxIdStr)								# Host sendet an Bootloader-RX-ID
			receiveId = _parseCanId(txIdStr)								# Host empfaengt von Bootloader-TX-ID
		except (ValueError, TypeError):
			return html.Span("Fehler: Ung\u00fcltige CAN-ID eingegeben.", style={"color": "var(--err-strong)"}), True, None, None

		if not canManager.isRunning:
			return html.Span(
				"Fehler: CAN-Bus nicht verbunden. Bitte zuerst im Konfigurationsfeld verbinden.",
				style={"color": "var(--err-strong)"},
			), True, None, None

		# OpenBLT-Geraet zum verbundenen Adapter ermitteln
		cfg = canManager.config
		deviceName, deviceChannel = _openbltDevice(cfg.interface, cfg.channel)

		if not deviceName:
			return html.Span(
				f"Fehler: Interface '{cfg.interface}' wird von OpenBLT nicht unterst\u00fctzt "
				f"(unterst\u00fctzt: {', '.join(_INTERFACE_MAP.keys())}).",
				style={"color": "var(--err-strong)"},
			), True, None, None

		# Datei dekodieren und temporaer speichern
		try:
			_, b64 = contents.split(",", 1)
			fileBytes = base64.b64decode(b64)
		except Exception as exc:
			return html.Span(f"Fehler beim Lesen der Datei: {exc}", style={"color": "var(--err-strong)"}), True, None, None

		try:
			with tempfile.NamedTemporaryFile(suffix=".srec", delete=False) as f:
				tmpPath = f.name
				f.write(fileBytes)
		except Exception as exc:
			return html.Span(f"Fehler beim Speichern der Datei: {exc}", style={"color": "var(--err-strong)"}), True, None, None

		# Alle Pruefungen bestanden, Zustand initialisieren und an den Hintergrund-Thread uebergeben
		_setState(
			running=True, phase="connecting", result=None,
			eraseDone=0, eraseTotal=1, writeDone=0, writeTotal=1,
		)

		# OpenBLT braucht exklusiven Zugriff, Empfangsthread vorher anhalten
		canManager.stop()
		time.sleep(0.5)

		threading.Thread(
			target=_flashThread,
			args=(tmpPath, filename, canManager, cfg, latest, lock, deviceName, deviceChannel, transmitId, receiveId),
			daemon=True,
		).start()

		# Vorherigen Fehlertext loeschen, Poll-Intervall aktivieren
		return "", False, None, None

	# Fortschritt waehrend des Flash-Vorgangs anzeigen
	@app.callback(
		Output("flash_progress_area", "children"),
		Output("flash_poll", "disabled", allow_duplicate=True),
		Input("flash_poll", "n_intervals"),
		prevent_initial_call=True,
	)
	def _pollFlashProgress (_):
		phase = _flashState["phase"]
		if phase == "idle":
			raise PreventUpdate
		if phase == "done":
			return _flashState["result"], True

		return _progressBarUi(), False
#-----------------------------------------------------------------------
