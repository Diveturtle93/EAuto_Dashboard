#-----------------------------------------------------------------------
# Titel		:	can_config.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	16.06.2026
# Version	:	1.0
# Autor		:	Diveturtle93
# Projekt	:	EAuto_Dashboard
# Quelle	:
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------
import can
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------
from backend.can_bus import CanConfig
from ui.header import formatCanStatus
#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_CAN_CONFIG								= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
CAN_CONFIG_MAJOR								= 1
CAN_CONFIG_MINOR								= 0
CAN_CONFIG_PATCH								= 0
CAN_CONFIG_DEV									= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
_FIELDS_VISIBLE									= {"display": "flex", "alignItems": "center", "gap": "8px", "flexWrap": "wrap"}
_FIELDS_HIDDEN									= {"display": "none"}
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Callback fuer den Verbinden/Trennen-Button des CAN-Adapters registrieren
#-----------------------------------------------------------------------
def registerCanConfigCallback (app, canManager, latest, lock):
	# CAN-Adapter verbinden bzw. trennen
	@app.callback(
		Output("btn_can_connect", "children"),
		Output("btn_can_connect", "className"),
		Output("can_connect_status", "children"),
		Output("can_connected", "data"),
		Output("can_config_fields", "style"),
		Input("btn_can_connect", "n_clicks"),
		State("can_interface", "value"),
		State("can_channel", "value"),
		State("can_bitrate", "value"),
		State("can_connected", "data"),
		prevent_initial_call=True,
	)
	def _toggleCan (nClicks, interface, channel, bitrate, isConnected):
		if not nClicks:
			raise PreventUpdate

		# Verbunden: Empfang stoppen und trennen
		if isConnected:
			canManager.stop()
			with lock:
				latest["last_rx_ms"] = 0
				latest["can_adapter_connected"] = False
			return "Verbinden", "btn", "Getrennt.", False, _FIELDS_VISIBLE

		if not interface or not channel or not bitrate:
			return "Verbinden", "btn", "Bitte Interface, Kanal und Baudrate ausw\u00e4hlen.", False, _FIELDS_VISIBLE

		# Synchroner Verbindungstest, schlaegt sofort fehl, wenn kein Adapter vorhanden ist
		try:
			testBus = can.Bus(interface=interface, channel=str(channel), bitrate=int(bitrate))
			testBus.shutdown()
		except (can.CanError, OSError, ValueError) as e:
			return "Verbinden", "btn", f"Kein Adapter gefunden: {e}", False, _FIELDS_VISIBLE

		# Empfang starten
		config = CanConfig(interface, str(channel), int(bitrate))
		canManager.start(config, latest, lock)
		return (
			"Trennen",
			"btn-danger",
			f"Verbunden: {interface} / {channel} @ {bitrate // 1000} kbit/s",
			True,
			_FIELDS_HIDDEN,
		)
#-----------------------------------------------------------------------

# Callback fuer die CAN-Status-Pille in der Titelleiste registrieren
#-----------------------------------------------------------------------
def registerCanBannerCallback (app):
	# CAN-Status bei jedem Snapshot neu darstellen
	@app.callback(
		Output("can_status_indicator", "children"),
		Input("snap", "data"),
		Input("can_connected", "data"),
	)
	def _updateCanStatus (snap, isConnected):
		return formatCanStatus(snap, isConnected)
#-----------------------------------------------------------------------
