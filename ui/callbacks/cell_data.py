#-----------------------------------------------------------------------
# Titel		:	cell_data.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	29.06.2026
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
from dash import Input, Output, Patch
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_CELL_DATA									= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
CELL_DATA_MAJOR									= 1
CELL_DATA_MINOR									= 0
CELL_DATA_PATCH									= 0
CELL_DATA_DEV									= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
_NUM_MODULES									= 10						# Anzahl Module
_CELLS											= 12						# Zellen pro Modul
_SENSORS										= 16						# Temperatursensoren pro Modul

_CHART_IDS										= ["cell_voltage_heatmap", "cell_temp_heatmap"]

# Clientside-JS: laeuft NACH dem Theme-Callback (verkettet ueber theme-dummy),
# liest --chart-text und --chart-grid aus dem CSS und setzt sie in allen Charts.
# Die Hintergruende sind in Python transparent, damit die Karte durchscheint.
_RELAYOUT_JS									= """
function(_) {
    var style = getComputedStyle(document.documentElement);
    var text = style.getPropertyValue('--chart-text').trim();
    var grid = style.getPropertyValue('--chart-grid').trim();
    if (!text) return '';
    var layout = {
        'font.color':      text,
        'xaxis.color':     text,
        'xaxis.gridcolor': grid,
        'xaxis.linecolor': grid,
        'yaxis.color':     text,
        'yaxis.gridcolor': grid,
        'yaxis.linecolor': grid,
        'yaxis.title.font.color': text
    };
    %s.forEach(function(gid) {
        try {
            var el = document.getElementById(gid);
            if (el) Plotly.relayout(el, layout);
        } catch(e) {}
    });
    return '';
}
""" % str(_CHART_IDS)
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Callbacks fuer die Zellspannungs- und Zelltemperatur-Charts registrieren
#-----------------------------------------------------------------------
def registerCellDataCallbacks (app):
	# Chart-Farben passend zum Theme setzen (clientside, aus dem CSS)
	app.clientside_callback(
		_RELAYOUT_JS,
		Output("chart-theme-dummy", "children"),
		Input("theme-dummy", "children"),
	)

	# Zellspannungen und Statistik aktualisieren
	@app.callback(
		Output("cell_voltage_heatmap", "figure"),
		Output("v_stat_min", "children"),
		Output("v_stat_max", "children"),
		Output("v_stat_delta", "children"),
		Output("v_stat_avg", "children"),
		Input("snap", "data"),
		prevent_initial_call=True,
	)
	def _updateVoltages (snap):
		patch = Patch()
		if not snap:
			patch["data"][0]["y"] = [None] * (_NUM_MODULES * _CELLS)
			return patch, "\u2013", "\u2013", "\u2013", "\u2013"

		L = snap.get("L", {})
		y = [L.get(f"cell_v_m{m}_c{c}") for m in range(_NUM_MODULES) for c in range(_CELLS)]
		patch["data"][0]["y"] = y

		vals = [v for v in y if v is not None]
		if not vals:
			return patch, "\u2013", "\u2013", "\u2013", "\u2013"

		mn, mx = min(vals), max(vals)
		avg = round(sum(vals) / len(vals))
		return patch, str(mn), str(mx), str(mx - mn), str(avg)

	# Zelltemperaturen und Statistik aktualisieren
	@app.callback(
		Output("cell_temp_heatmap", "figure"),
		Output("t_stat_min", "children"),
		Output("t_stat_max", "children"),
		Output("t_stat_avg", "children"),
		Input("snap", "data"),
		prevent_initial_call=True,
	)
	def _updateTemperatures (snap):
		patch = Patch()
		if not snap:
			patch["data"][0]["y"] = [None] * (_NUM_MODULES * _SENSORS)
			return patch, "\u2013", "\u2013", "\u2013"

		L = snap.get("L", {})
		y = [L.get(f"cell_t_m{m}_s{s}") for m in range(_NUM_MODULES) for s in range(_SENSORS)]
		patch["data"][0]["y"] = y

		vals = [v for v in y if v is not None]
		if not vals:
			return patch, "\u2013", "\u2013", "\u2013"

		mn, mx = min(vals), max(vals)
		avg = round(sum(vals) / len(vals))
		return patch, str(mn), str(mx), str(avg)
#-----------------------------------------------------------------------
