#-----------------------------------------------------------------------
# Titel		:	export_csv.py
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
import csv
import io
from datetime import datetime
#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------
from dash import Input, Output, State, dcc
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_EXPORT_CSV								= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
EXPORT_CSV_MAJOR								= 1
EXPORT_CSV_MINOR								= 0
EXPORT_CSV_PATCH								= 0
EXPORT_CSV_DEV									= 0
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Callback fuer den CSV-Export registrieren
#-----------------------------------------------------------------------
def registerExportCsvCallback (app):
	# Aktuellen Snapshot als CSV-Datei zum Download anbieten
	@app.callback(
		Output("dl", "data"),
		Input("btn_csv", "n_clicks"),
		State("snap", "data"),
		prevent_initial_call=True,
	)
	def _exportCsv (_n, snap):
		if snap is None:
			return None

		buf = io.StringIO()
		writer = csv.writer(buf)

		# Je Key eine Zeile, Listen mit ; getrennt
		L = snap.get("L", snap)
		writer.writerow(["key", "value"])
		for k, v in L.items():
			val = ";".join(map(str, v)) if isinstance(v, (list, tuple)) else str(v)
			writer.writerow([k, val])

		fname = f"EAuto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
		return dcc.send_string(buf.getvalue(), filename=fname)

	return _exportCsv
#-----------------------------------------------------------------------
