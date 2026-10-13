#-----------------------------------------------------------------------
# Titel		:	dashboard_tab.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	28.06.2026
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
from dash import dcc, html
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_DASHBOARD_TAB								= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
DASHBOARD_TAB_MAJOR								= 1
DASHBOARD_TAB_MINOR								= 0
DASHBOARD_TAB_PATCH								= 0
DASHBOARD_TAB_DEV								= 0
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Zeitfenster-Auswahl sowie Export- und Reset-Button aufbauen
#-----------------------------------------------------------------------
def buildTimeWindowControls ():
	return html.Div(
		children=[
			html.Div(
				className="card",
				style={
					"display": "flex",
					"alignItems": "center",
					"gap": "18px",
					"flexWrap": "wrap",
				},
				children=[
					html.P("Time Window", className="card-sec", style={"marginBottom": "0"}),
					dcc.RadioItems(
						id="win_sel",
						options=[
							{"label": "  1 min", "value": 60},
							{"label": "  5 min", "value": 300},
							{"label": "  30 min", "value": 1800},
							{"label": "  All", "value": 0},
						],
						value=0,
						inline=True,
						inputStyle={"accentColor": "var(--accent)", "cursor": "pointer"},
						labelStyle={
							"fontSize": "12px",
							"color": "var(--text-secondary)",
							"cursor": "pointer",
							"userSelect": "none",
						},
					),
					html.Button(
						"Export CSV",
						id="btn_csv",
						className="btn",
						style={"marginLeft": "auto"},
					),
					html.Button(
						"Reset",
						id="btn_reset",
						className="btn-danger",
					),
				],
			),
			html.P(
				"Tip: scroll to zoom on any graph. Double-click to reset.",
				style={"color": "var(--text-muted)", "fontSize": "11px", "marginTop": "4px"},
			),
		]
	)
#-----------------------------------------------------------------------
