#-----------------------------------------------------------------------
# Titel		:	temperature_chart.py
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

#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------
import plotly.graph_objects as go
from dash import Input, Output, Patch, dcc
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_TEMPERATURE_CHART							= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
TEMPERATURE_CHART_MAJOR							= 1
TEMPERATURE_CHART_MINOR							= 0
TEMPERATURE_CHART_PATCH							= 0
TEMPERATURE_CHART_DEV							= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
_ADC_MAX										= 4095						# 12-Bit ADC
_LABELS											= ["T1", "T2", "T3", "T4"]
_COLORS											= ["#f97316", "#60a5fa", "#34d399", "#f87171"]
_LAYOUT											= dict(
	yaxis=dict(
		range=[0, _ADC_MAX], title="ADC-Wert (12-bit)",
		color="#9099a8", gridcolor="#252836", linecolor="#252836", zerolinecolor="#252836",
	),
	xaxis=dict(
		title="Temperatursensor",
		color="#9099a8", gridcolor="#252836", linecolor="#252836",
	),
	margin=dict(t=30, b=40, l=50, r=20),
	plot_bgcolor="#161922",
	paper_bgcolor="#161922",
	font=dict(color="#9099a8"),
	height=280,
	showlegend=False,
)
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Statischen dcc.Graph fuer das Layout aufbauen, Daten kommen per Patch()
#-----------------------------------------------------------------------
def buildTemperatureGraph ():
	fig = go.Figure(
		go.Bar(
			x=_LABELS, y=[0, 0, 0, 0], marker_color=_COLORS,
			text=["\u2013", "\u2013", "\u2013", "\u2013"], textposition="outside",
		),
	)
	fig.update_layout(**_LAYOUT)

	return dcc.Graph(id="temperature_graph", figure=fig, config={"displayModeBar": False})
#-----------------------------------------------------------------------

# Callback fuer das Temperatur-Balkendiagramm registrieren
#-----------------------------------------------------------------------
def registerTemperatureChartCallback (app):
	# ADC-Werte der Temperatursensoren aktualisieren
	@app.callback(
		Output("temperature_graph", "figure"),
		Input("snap", "data"),
		prevent_initial_call=True,
	)
	def updateTemperatureChart (snap):
		patch = Patch()
		if not snap:
			patch["data"][0]["y"] = [0, 0, 0, 0]
			patch["data"][0]["text"] = ["\u2013", "\u2013", "\u2013", "\u2013"]
			return patch

		L = snap.get("L", {})
		raw = [L.get(f"temp_adc_{i}") for i in range(1, 5)]
		patch["data"][0]["y"] = [v if v is not None else 0 for v in raw]
		patch["data"][0]["text"] = [str(v) if v is not None else "\u2013" for v in raw]
		return patch
#-----------------------------------------------------------------------
