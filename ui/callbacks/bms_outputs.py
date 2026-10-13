#-----------------------------------------------------------------------
# Titel		:	bms_outputs.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	06.07.2026
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
from dash import Input, Output
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------
from ui.cards.bms_outputs_card import ALL_OUTPUT_FIELDS, DOT_STYLE
#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_BMS_OUTPUTS								= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
BMS_OUTPUTS_MAJOR								= 1
BMS_OUTPUTS_MINOR								= 0
BMS_OUTPUTS_PATCH								= 0
BMS_OUTPUTS_DEV									= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
_ON_COLOR										= "var(--ok-alt)"			# Ausgang an
_OFF_COLOR										= "var(--err-strong)"		# Ausgang aus
_UNKNOWN_COLOR									= "var(--text-inactive)"	# Noch kein Wert empfangen
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Callback fuer die Statuspunkte der BMS GPIO-Ausgaenge registrieren
#-----------------------------------------------------------------------
def registerBmsOutputsCallback (app):
	# Farbe jedes Statuspunkts aus dem aktuellen Snapshot setzen
	@app.callback(
		[Output(f"bms_out_dot_{field}", "style") for field in ALL_OUTPUT_FIELDS],
		Input("snap", "data"),
		prevent_initial_call=True,
	)
	def _updateBmsOutputs (snap):
		L = (snap or {}).get("L", {})
		styles = []
		for field in ALL_OUTPUT_FIELDS:
			val = L.get(field)
			if val == 1:
				color = _ON_COLOR
			elif val == 0:
				color = _OFF_COLOR
			else:
				color = _UNKNOWN_COLOR
			styles.append({**DOT_STYLE, "background": color})

		return styles
#-----------------------------------------------------------------------
