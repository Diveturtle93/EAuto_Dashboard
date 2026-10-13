#-----------------------------------------------------------------------
# Titel		:	ecu_preset.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	18.06.2026
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
from dash.exceptions import PreventUpdate
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_ECU_PRESET								= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
ECU_PRESET_MAJOR								= 1
ECU_PRESET_MINOR								= 0
ECU_PRESET_PATCH								= 0
ECU_PRESET_DEV									= 0
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Callback fuer die Steuergeraete-Auswahl registrieren
#-----------------------------------------------------------------------
def registerEcuPresetCallback (app):
	# CAN-ID-Felder aus dem gewaehlten Preset "rx|tx" befuellen
	@app.callback(
		Output("bootloader_rx_id", "value"),
		Output("bootloader_tx_id", "value"),
		Input("ecu_preset", "value"),
		prevent_initial_call=True,
	)
	def _applyPreset (preset):
		if not preset:
			raise PreventUpdate

		rx, tx = preset.split("|")
		return rx, tx
#-----------------------------------------------------------------------
