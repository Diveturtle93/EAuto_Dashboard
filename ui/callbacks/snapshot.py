#-----------------------------------------------------------------------
# Titel		:	snapshot.py
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
import time
#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------
from dash import Input, Output
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_SNAPSHOT									= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
SNAPSHOT_MAJOR									= 1
SNAPSHOT_MINOR									= 0
SNAPSHOT_PATCH									= 0
SNAPSHOT_DEV									= 0
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Callback fuer den periodischen Snapshot registrieren
#-----------------------------------------------------------------------
def registerSnapshotCallback (app, lock, latest):
	# Bei jedem Tick eine Kopie von latest in den dcc.Store schreiben
	@app.callback(
		Output("snap", "data"),
		Input("tick", "n_intervals"),
	)
	def _snapshot (_):
		with lock:
			L = latest.copy()

		return dict(
			L=L,
			now=time.time(),
			mono_now=time.monotonic(),
		)

	return _snapshot
#-----------------------------------------------------------------------
