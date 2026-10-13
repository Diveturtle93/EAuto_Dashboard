#-----------------------------------------------------------------------
# Titel		:	eauto_dashboard.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	16.06.2026
# Version	:	1.0
# Autor		:	Diveturtle93
# Projekt	:	EAuto_Dashboard
# Quelle	:
#-----------------------------------------------------------------------

# Beschreibung
#-----------------------------------------------------------------------
# EAuto Live Dashboard, Windows-Version mit python-can als CAN-Schnittstelle.
# Unterstuetzt PCAN, Vector, Kvaser und weitere CAN-Adapter unter Windows.
#
# Abhaengigkeiten installieren:
#   pip install dash plotly python-can
#
# Aufruf:
#   python eauto_dashboard.py [interface] [channel] [bitrate]
#
# Die Argumente fuellen nur die CAN-Konfiguration im Browser vor, der Adapter
# wird erst nach Klick auf "Verbinden" verbunden. Beispiele:
#   python eauto_dashboard.py pcan PCAN_USBBUS1 500000
#   python eauto_dashboard.py vector 0 500000
#   python eauto_dashboard.py slcan COM3 500000
#
# Danach im Browser http://localhost:8051 oeffnen.
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------
import sys
import threading
#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------
from dash import Dash, dcc, html
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------
from backend.can_bus import CAN_Manager
from ui.bootloader import buildFirmwareUploadCard
from ui.callbacks import (
	registerBmsOutputsCallback,
	registerCanBannerCallback,
	registerCanConfigCallback,
	registerCellDataCallbacks,
	registerEcuPresetCallback,
	registerExportCsvCallback,
	registerFirmwareUploadCallback,
	registerResetCallback,
	registerSnapshotCallback,
	registerThemeCallback,
)
from ui.cards import buildBmsOutputsCard
from ui.cell_data_tab import buildCellDataTab
from ui.dashboard_tab import buildTimeWindowControls
from ui.header import buildCanConfigFields, buildThemeButton
#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_EAUTO_DASHBOARD							= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
EAUTO_DASHBOARD_MAJOR							= 1
EAUTO_DASHBOARD_MINOR							= 0
EAUTO_DASHBOARD_PATCH							= 0
EAUTO_DASHBOARD_DEV								= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
# Kommandozeilen-Argumente, fuellen nur die UI vor (kein automatisches Verbinden)
DEFAULT_INTERFACE								= sys.argv[1] if len(sys.argv) > 1 else "pcan"
DEFAULT_CHANNEL									= sys.argv[2] if len(sys.argv) > 2 else "PCAN_USBBUS1"
DEFAULT_BITRATE									= int(sys.argv[3]) if len(sys.argv) > 3 else 500000
INTERVAL										= 500						# Aktualisierung Dashboard in ms

# Layout-Bausteine
_CARD											= {
	"background": "var(--bg-card)",
	"borderRadius": "10px",
	"boxShadow": "0 1px 8px var(--shadow-card)",
	"border": "1px solid var(--border)",
	"padding": "12px 14px",
	"marginBottom": "14px",
}
_TAB_STYLE										= {
	"background": "var(--bg-page)", "color": "var(--text-secondary)",
	"border": "1px solid var(--border)", "padding": "6px 16px", "fontSize": "13px",
}
_TAB_SELECTED									= {
	"background": "var(--bg-card)", "color": "var(--accent)",
	"borderTop": "2px solid var(--accent)", "border": "1px solid var(--border)",
	"padding": "6px 16px", "fontSize": "13px",
}
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------
lock = threading.Lock()														# Schutz fuer latest

# Datenspeicher, projektspezifische Felder hier ergaenzen
latest = dict(
	last_rx_ms=0,
	can_adapter_connected=False,
	_can_rx_ts={},
)

app = Dash(__name__)														# Dash-Anwendung
#-----------------------------------------------------------------------

# Layout des Dashboards aufbauen
#-----------------------------------------------------------------------
def buildLayout ():
	return html.Div(
		style={
			"fontFamily": "'Inter', 'Segoe UI', sans-serif",
			"background": "var(--bg-page)", "minHeight": "100vh", "padding": "14px 24px",
			"maxWidth": "1300px", "margin": "0 auto", "color": "var(--text)",
		},
		children=[
			# Seitentitel und CAN-Konfiguration
			html.Div(
				style={
					**_CARD, "marginBottom": "14px", "padding": "10px 14px",
					"display": "flex", "alignItems": "center",
					"gap": "16px", "flexWrap": "wrap",
				},
				children=[
					html.H2(
						"EAuto Live Dashboard",
						style={
							"margin": "0", "fontSize": "16px", "color": "var(--text)",
							"fontWeight": "700", "whiteSpace": "nowrap",
						},
					),
					html.Div(style={"flex": "1"}),
					buildCanConfigFields(DEFAULT_INTERFACE, DEFAULT_CHANNEL, DEFAULT_BITRATE),
					html.Div(id="can_status_indicator"),
					buildThemeButton(),
				],
			),

			# Tabs
			dcc.Tabs(
				id="main_tabs",
				value="tab_dashboard",
				style={"marginBottom": "14px"},
				colors={"border": "var(--border)", "primary": "var(--accent)", "background": "var(--bg-page)"},
				children=[
					dcc.Tab(
						label="Dashboard",
						value="tab_dashboard",
						style=_TAB_STYLE,
						selected_style=_TAB_SELECTED,
						children=[
							html.Div(style={"paddingTop": "14px"}, children=[
								buildTimeWindowControls(),
								buildBmsOutputsCard(),
								# Eigene Anzeigen hier einfuegen
							]),
						],
					),
					dcc.Tab(
						label="Zellen",
						value="tab_zellen",
						style=_TAB_STYLE,
						selected_style=_TAB_SELECTED,
						children=[buildCellDataTab()],
					),
					dcc.Tab(
						label="Bootloader",
						value="tab_bootloader",
						style=_TAB_STYLE,
						selected_style=_TAB_SELECTED,
						children=[
							html.Div(style={"paddingTop": "14px"}, children=[
								buildFirmwareUploadCard(),
							]),
						],
					),
				],
			),

			dcc.Interval(id="tick", interval=INTERVAL, n_intervals=0),
			dcc.Store(id="snap", storage_type="memory"),
			dcc.Store(id="theme-store", data="dark", storage_type="local"),
			dcc.Download(id="dl"),
			html.Div(id="reset_dummy", style={"display": "none"}),
			html.Div(id="theme-dummy", style={"display": "none"}),
			html.Div(id="chart-theme-dummy", style={"display": "none"}),
		],
	)
#-----------------------------------------------------------------------

# Alle Callbacks registrieren
#-----------------------------------------------------------------------
def registerCallbacks ():
	registerSnapshotCallback(app, lock, latest)
	registerResetCallback(app, lock, latest)
	registerCanBannerCallback(app)
	registerCanConfigCallback(app, CAN_Manager, latest, lock)
	registerCellDataCallbacks(app)
	registerBmsOutputsCallback(app)
	registerEcuPresetCallback(app)
	registerExportCsvCallback(app)
	registerFirmwareUploadCallback(app, CAN_Manager, latest, lock)
	registerThemeCallback(app)
#-----------------------------------------------------------------------

# Hauptprogramm
#-----------------------------------------------------------------------
if __name__ == "__main__":
	app.layout = buildLayout()
	registerCallbacks()

	print("=" * 60)
	print("  EAuto Live Dashboard (Windows)")
	print(f"  Standardwerte: {DEFAULT_INTERFACE} / {DEFAULT_CHANNEL} @ {DEFAULT_BITRATE} bps")
	print(f"  CAN-Adapter bitte im Browser verbinden.")
	print(f"  Dashboard: http://localhost:8051")
	print("=" * 60)
	app.run(host="127.0.0.1", port=8051, debug=False)
#-----------------------------------------------------------------------
