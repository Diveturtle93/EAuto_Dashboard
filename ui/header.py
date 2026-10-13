#-----------------------------------------------------------------------
# Titel		:	header.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	28.06.2026
# Version	:	1.0
# Autor		:	Diveturtle93
# Projekt	:	EAuto_Dashboard
# Quelle	:
#-----------------------------------------------------------------------

# Beschreibung
#-----------------------------------------------------------------------
# Layout-Bausteine fuer die Titelleiste des Dashboards: Theme-Umschalter,
# CAN-Adapter-Konfigurationsfelder (Interface/Kanal/Bitrate + Verbinden-Button)
# sowie die CAN-Status-Pille. Die zugehoerige Logik liegt in
# ui/callbacks/theme.py bzw. ui/callbacks/can_config.py.
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------
from dash import dcc, html
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_HEADER									= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
HEADER_MAJOR									= 1
HEADER_MINOR									= 0
HEADER_PATCH									= 0
HEADER_DEV										= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
_INPUT											= {
	"width": "100%",
	"padding": "7px 10px",
	"borderRadius": "6px",
	"border": "1px solid var(--border)",
	"background": "var(--bg-page)",
	"color": "var(--text)",
	"fontSize": "13px",
	"boxSizing": "border-box",
}

_INTERFACES										= ["pcan", "vector", "kvaser", "slcan", "ixxat", "usb2can", "socketcan"]

_BITRATES										= [
	{"label": "125 kbit/s", "value": 125000},
	{"label": "250 kbit/s", "value": 250000},
	{"label": "500 kbit/s", "value": 500000},
	{"label": "1 Mbit/s", "value": 1000000},
]
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Theme-Umschalter, die Aufschrift zeigt, wohin der naechste Klick wechselt
#-----------------------------------------------------------------------
def buildThemeButton ():
	return html.Button(
		"Dunkel",
		id="theme-btn",
		n_clicks=0,
		className="btn",
	)
#-----------------------------------------------------------------------

# CAN-Adapter-Konfigurationsfelder, kompakte Inline-Darstellung fuer die Titelleiste
#-----------------------------------------------------------------------
def buildCanConfigFields (defaultInterface="pcan", defaultChannel="PCAN_USBBUS1", defaultBitrate=500000):
	inputCompact = {**_INPUT, "padding": "5px 8px", "fontSize": "12px", "width": "130px"}

	return html.Div(
		style={"display": "flex", "alignItems": "center", "gap": "8px", "flexWrap": "wrap"},
		children=[
			html.Div(
				id="can_config_fields",
				style={"display": "flex", "alignItems": "center", "gap": "8px", "flexWrap": "wrap"},
				children=[
					dcc.Dropdown(
						id="can_interface",
						options=[{"label": i, "value": i} for i in _INTERFACES],
						value=defaultInterface,
						clearable=False,
						style={"fontSize": "12px", "width": "120px"},
					),
					dcc.Input(
						id="can_channel",
						type="text",
						value=defaultChannel,
						debounce=True,
						style=inputCompact,
					),
					dcc.Dropdown(
						id="can_bitrate",
						options=_BITRATES,
						value=defaultBitrate,
						clearable=False,
						style={"fontSize": "12px", "width": "120px"},
					),
				],
			),
			html.Button(
				"Verbinden",
				id="btn_can_connect",
				n_clicks=0,
				className="btn",
			),
			html.Div(id="can_connect_status", style={"fontSize": "12px", "color": "var(--text-secondary)"}),
			dcc.Store(id="can_connected", data=False),
		],
	)
#-----------------------------------------------------------------------

# CAN-Status-Pille fuer die Titelleiste (4 Zustaende: grau/gelb/gruen/rot)
# snap: Dict mit "L" (latest-Snapshot) und "now" (aktueller Zeitstempel)
# isConnected: CanManager hat aktuell einen laufenden Empfangsthread
#-----------------------------------------------------------------------
def formatCanStatus (snap, isConnected):
	# Grau: kein CAN-Adapter konfiguriert/verbunden
	if not isConnected:
		return _pill("Kein Adapter", "var(--bg-subtle)", "var(--text-inactive)", "var(--text-muted)")

	# Gelb: Adapter wurde nach Verbindungsaufbau getrennt (Reconnect laeuft)
	L = snap.get("L", {}) if snap else {}
	if not L.get("can_adapter_connected", False):
		return _pill("Adapter getrennt", "var(--warn-bg)", "var(--warn)", "var(--warn)")

	# Gruen: verbunden, aber noch keine Nachricht empfangen
	lastRx = L.get("last_rx_ms", 0)
	if lastRx == 0:
		return _pill("CAN OK", "var(--ok-alt-bg)", "var(--ok-alt)", "var(--ok-alt)")

	# Gruen: zuletzt empfangener Frame ist noch frisch
	pktAge = snap["now"] - lastRx / 1000.0
	if pktAge < 3.0:
		return _pill("CAN OK", "var(--ok-alt-bg)", "var(--ok-alt)", "var(--ok-alt)")

	# Rot: seit > 3 s keine CAN-Nachricht mehr empfangen
	return _pill(f"CAN Fehler ({pktAge:.0f} s)", "var(--err-bg)", "var(--err-strong)", "var(--err-text)")
#-----------------------------------------------------------------------

# Kleine, farbige Status-Pille (Punkt + Text) bauen
#-----------------------------------------------------------------------
def _pill (text, bg, dot, textColor):
	return html.Div(
		children=[
			html.Span(style={
				"display": "inline-block", "width": "8px", "height": "8px",
				"borderRadius": "50%", "background": dot,
				"marginRight": "6px", "flexShrink": "0",
			}),
			html.Span(text, style={"fontSize": "12px", "fontWeight": "600", "color": textColor}),
		],
		style={
			"display": "inline-flex", "alignItems": "center",
			"padding": "5px 12px", "borderRadius": "20px",
			"background": bg, "border": f"1px solid {dot}",
			"whiteSpace": "nowrap",
		},
	)
#-----------------------------------------------------------------------
