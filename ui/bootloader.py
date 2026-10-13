#-----------------------------------------------------------------------
# Titel		:	bootloader.py
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
from dash import dcc, html
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_BOOTLOADER								= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
BOOTLOADER_MAJOR								= 1
BOOTLOADER_MINOR								= 0
BOOTLOADER_PATCH								= 0
BOOTLOADER_DEV									= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
_LABEL											= {
	"fontSize": "11px",
	"fontWeight": "700",
	"color": "var(--text-secondary)",
	"marginBottom": "4px",
}

# (Name, Bootloader-RX-ID, Bootloader-TX-ID)
ECU_PRESETS										= [
	("BMS", "0x7E0", "0x7E1"),
	("Charger", "0x66A", "0x7E4"),
	("HBT", "0x66B", "0x7E5"),
	("MBT", "0x66C", "0x7E6"),
	("SOC Display", "0x66D", "0x7E7"),
	("Display 1", "0x66E", "0x7EE"),
	("Display 2", "0x66F", "0x7EF"),
]
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Karte fuer den Firmware-Upload mit Anleitung, ECU-Auswahl und CAN-IDs aufbauen
#-----------------------------------------------------------------------
def buildFirmwareUploadCard ():
	return html.Div(
		className="card",
		children=[
			html.P("Firmware Update", className="card-sec", style={"marginBottom": "8px"}),
			dcc.Upload(
				id="firmware_upload",
				children=html.Div([
					"Firmware-Datei hierhin ziehen oder klicken, um sie auszuw\u00e4hlen."
				]),
				style={
					"width": "100%",
					"maxWidth": "100%",
					"boxSizing": "border-box",
					"margin": "0 auto",
					"padding": "16px",
					"borderWidth": "1px",
					"borderStyle": "dashed",
					"borderRadius": "10px",
					"borderColor": "var(--border-faint)",
					"backgroundColor": "var(--bg-page)",
					"textAlign": "center",
					"color": "var(--text-secondary)",
					"cursor": "pointer",
					"overflow": "hidden",
				},
				multiple=False,
			),

			# Anleitung
			html.Div(
				style={
					"background": "var(--bg-raised)",
					"border": "1px solid var(--border-info)",
					"borderRadius": "8px",
					"padding": "14px 16px",
					"marginTop": "12px",
					"fontSize": "12px",
					"color": "var(--text-secondary)",
					"lineHeight": "1.7",
				},
				children=[
					html.P(
						"So wird ein Update durchgef\u00fchrt:",
						style={"fontWeight": "700", "margin": "0 0 6px 0", "fontSize": "12px", "color": "var(--text)"},
					),
					html.Ol(
						children=[
							html.Li("Firmware-Datei (.srec) oben in das Upload-Feld ziehen oder per Klick ausw\u00e4hlen."),
							html.Li("Das Steuerger\u00e4t wechselt automatisch in den Bootloader-Modus, sobald es die erste Bootloader-Nachricht empf\u00e4ngt \u2013 ein manueller Reset oder Power-Cycle ist nicht erforderlich."),
							html.Li("Der Upload startet automatisch, sobald der Bootloader erkannt wird (Wartezeit bis zu 30 s)."),
							html.Li("Den Fortschritt und etwaige Fehlermeldungen im Statusbereich unterhalb der Schaltfl\u00e4che verfolgen."),
						],
						style={"margin": "0 0 10px 0", "paddingLeft": "18px"},
					),
					html.P(
						"Bedeutung der CAN-IDs:",
						style={"fontWeight": "700", "margin": "0 0 4px 0", "fontSize": "12px", "color": "var(--text)"},
					),
					html.Ul(
						children=[
							html.Li([
								html.Strong("Bootloader RX CAN-ID:"),
								" CAN-ID, \u00fcber die das Dashboard Befehle an den Bootloader im Steuerger\u00e4t sendet. "
								"Muss mit der im Steuerger\u00e4t konfigurierten Master-TX-ID \u00fcbereinstimmen.",
							]),
							html.Li([
								html.Strong("Bootloader TX CAN-ID:"),
								" CAN-ID, \u00fcber die der Bootloader Antworten an das Dashboard zur\u00fccksendet. "
								"Muss mit der im Steuerger\u00e4t konfigurierten Master-RX-ID \u00fcbereinstimmen.",
							]),
						],
						style={"margin": "0", "paddingLeft": "18px"},
					),
				],
			),

			# Auswahl des Steuergeraets
			html.Div(
				style={"marginTop": "16px"},
				children=[
					html.Div("Steuerger\u00e4t", style=_LABEL),
					dcc.Dropdown(
						id="ecu_preset",
						options=(
							[{"label": "\u2013 Manuell \u2013", "value": ""}]
							+ [
								{"label": f"{name}  ({rx} / {tx})", "value": f"{rx}|{tx}"}
								for name, rx, tx in ECU_PRESETS
							]
						),
						value="",
						clearable=False,
						placeholder="Steuerger\u00e4t w\u00e4hlen \u2026",
						style={"fontSize": "13px"},
					),
				],
			),

			# Bootloader CAN-IDs
			html.Div(
				style={
					"display": "grid",
					"gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))",
					"gap": "12px",
					"marginTop": "12px",
				},
				children=[
					html.Div(children=[
						html.Div(
							"Bootloader RX CAN-ID",
							style={
								"fontSize": "11px",
								"fontWeight": "700",
								"color": "var(--text-secondary)",
								"marginBottom": "4px",
							},
						),
						dcc.Input(
							id="bootloader_rx_id",
							type="text",
							value="0x66E",
							style={
								"width": "100%",
								"padding": "8px 10px",
								"borderRadius": "6px",
								"border": "1px solid var(--border)",
								"background": "var(--bg-page)",
								"color": "var(--text)",
							},
						),
					]),
					html.Div(children=[
						html.Div(
							"Bootloader TX CAN-ID",
							style={
								"fontSize": "11px",
								"fontWeight": "700",
								"color": "var(--text-secondary)",
								"marginBottom": "4px",
							},
						),
						dcc.Input(
							id="bootloader_tx_id",
							type="text",
							value="0x7EE",
							style={
								"width": "100%",
								"padding": "8px 10px",
								"borderRadius": "6px",
								"border": "1px solid var(--border)",
								"background": "var(--bg-page)",
								"color": "var(--text)",
							},
						),
					]),
				],
			),

			# Fortschritt und Status
			dcc.Interval(id="flash_poll", interval=250, disabled=True, n_intervals=0),
			html.Div(id="flash_progress_area"),
			dcc.Loading(
				id="bootloader_loading",
				type="dot",
				children=html.Div(id="bootloader_status", style={"marginTop": "12px", "fontSize": "13px"}),
				style={"width": "100%", "paddingTop": "8px"},
			),
		],
	)
#-----------------------------------------------------------------------
