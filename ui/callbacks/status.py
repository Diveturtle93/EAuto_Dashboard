#-----------------------------------------------------------------------
# Titel		:	status.py
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
from dash import Input, Output, html
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_STATUS									= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
STATUS_MAJOR									= 1
STATUS_MINOR									= 0
STATUS_PATCH									= 0
STATUS_DEV										= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
STATUS_NAME										= {
	0: "Start",
	1: "Ready",
	2: "KL15",
	3: "Anlassen",
	4: "Precharge",
	5: "ReadyToDrive",
	6: "Drive",
	7: "Standby",
	8: "Ausschalten",
	9: "Laden",
}

COLOR_MAP										= {
	"Normal": "#2ecc71",													# Gruen
	"Warning": "#f1c40f",													# Gelb
	"Error": "#e74c3c",														# Rot
	"Critical Error": "#8e44ad",											# Lila
	"Invalid": "#95a5a6",													# Grau
	"Severe Error": "#c0392b",												# Kraeftiges Rot
	"Unknown": "#7f8c8d",
}
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Callback fuer die Statusanzeige von BMS und Motor registrieren
#-----------------------------------------------------------------------
def registerStatusCallback (app):
	# Ein Anzeigefeld mit Beschriftung und Wert aufbauen
	def makeField (label, value, background="#161922", color="#f0f1f5"):
		return html.Div(
			children=[
				html.Div(label, style={"fontSize": "12px", "fontWeight": "700", "marginBottom": "6px", "color": "#9099a8"}),
				html.Div(value, style={
					"background": background,
					"color": color,
					"padding": "12px",
					"borderRadius": "8px",
					"textAlign": "center",
					"fontWeight": "700",
				}),
			],
			style={"minWidth": "140px"},
		)

	# Zustand und Status von BMS und Motor anzeigen
	@app.callback(
		Output("status", "children"),
		Input("snap", "data"),
	)
	def _status (snap):
		if snap is None:
			return ""

		L = snap.get("L", {})
		bmsState = L.get("bms_state", "Unknown")
		bmsStatusCode = L.get("bms_status_code")
		motorState = L.get("motor_state", "Unknown")
		motorStatusCode = L.get("motor_status_code")

		# Statuscode mit Namen
		if isinstance(bmsStatusCode, int):
			bmsStatusText = f"{bmsStatusCode} \u2014 {STATUS_NAME.get(bmsStatusCode, str(bmsStatusCode))}"
		else:
			bmsStatusText = "--"

		if isinstance(motorStatusCode, int):
			motorStatusText = f"{motorStatusCode} \u2014 {STATUS_NAME.get(motorStatusCode, str(motorStatusCode))}"
		else:
			motorStatusText = "--"

		items = [
			makeField("BMS Zustand", bmsState, background=COLOR_MAP.get(bmsState, "#7f8c8d"), color="#fff"),
			makeField("BMS Status", bmsStatusText),
			makeField("Motorzustand", motorState, background=COLOR_MAP.get(motorState, "#7f8c8d"), color="#fff"),
			makeField("Motorstatus", motorStatusText),
		]

		return html.Div(items, style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "12px"})

	return _status
#-----------------------------------------------------------------------
