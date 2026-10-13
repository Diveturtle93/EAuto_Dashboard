#-----------------------------------------------------------------------
# Titel		:	bms_outputs_card.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	06.07.2026
# Version	:	1.0
# Autor		:	Diveturtle93
# Projekt	:	EAuto_Dashboard
# Quelle	:
#-----------------------------------------------------------------------

# Beschreibung
#-----------------------------------------------------------------------
# Karte mit Statusanzeige aller BMS GPIO-Ausgaenge (CAN 0x237). Jeder Ausgang
# wird als farbiger Punkt dargestellt: Rot = 0 (aus), Gruen = 1 (an). Wird per
# Callback (ui/callbacks/bms_outputs.py) bei jedem neuen Snapshot aktualisiert.
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------
from dash import html
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_BMS_OUTPUTS_CARD							= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
BMS_OUTPUTS_CARD_MAJOR							= 1
BMS_OUTPUTS_CARD_MINOR							= 0
BMS_OUTPUTS_CARD_PATCH							= 0
BMS_OUTPUTS_CARD_DEV							= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
# (Gruppentitel, [(Feldname aus can_0x237.py, Anzeigename), ...])
_GROUPS											= [
	("System", [
		("sys_ams_limit", "BMS Error"),
		("sys_imd_ok", "IMD Error"),
		("sys_ams_ok", "AMS-OK"),
		("sys_freigabe", "Freigabe RUN (Bamocar)"),
		("sys_recuperation", "Recuperation m\u00f6glich"),
		("sys_hv_p", "HV-Relais Positiv"),
		("sys_hv_n", "HV-Relais Negativ"),
		("sys_power_on", "Power ON"),
	]),
	("Highcurrent", [
		("hc_digital1", "Digitaler Ausgang 1"),
		("hc_digital2", "Digitaler Ausgang 2"),
		("hc_precharge_out", "Precharge Relais"),
		("hc_hv_m", "HV-Relais Zus\u00e4tzlich"),
		("hc_hv_chg", "HV-Relais Ladeger\u00e4t"),
		("hc_heater1", "Heizung 1"),
		("hc_heater2", "Heizung 2"),
	]),
	("LED", [
		("led_inlet_red", "Inlet LED Rot"),
		("led_inlet_green", "Inlet LED Gr\u00fcn"),
		("led_akku_error", "Akku Error LED"),
		("led_red", "PCB LED Rot"),
		("led_green", "PCB LED Gr\u00fcn"),
		("led_blue", "PCB LED Blau"),
	]),
	("Komfort", [
		("komfort_trigger_out", "Trigger Stromsensor"),
		("komfort_isospi_en", "IsoSPI Spannung"),
		("komfort_isohv_en", "Precharge Abfrage"),
	]),
]

# Alle Feldnamen in fester Reihenfolge, fuer den Callback (ein Output-Punkt je Feld)
ALL_OUTPUT_FIELDS								= [field for _, fields in _GROUPS for field, _ in fields]

DOT_STYLE										= {
	"display": "inline-block", "width": "10px", "height": "10px",
	"borderRadius": "50%", "marginRight": "8px", "flexShrink": "0",
	"background": "var(--text-inactive)",
}

_ITEM_STYLE										= {
	"display": "flex", "alignItems": "center",
	"padding": "4px 0", "fontSize": "12px", "color": "var(--text-secondary)",
}

_GROUP_TITLE_STYLE								= {
	"fontSize": "12px", "fontWeight": "700", "color": "var(--text-muted)",
	"margin": "0 0 6px 0", "textTransform": "uppercase", "letterSpacing": "0.03em",
}
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Eine Zeile mit Statuspunkt und Bezeichnung aufbauen
#-----------------------------------------------------------------------
def _outputItem (field, label):
	return html.Div(
		style=_ITEM_STYLE,
		children=[
			html.Span(style=DOT_STYLE, id=f"bms_out_dot_{field}"),
			html.Span(label),
		],
	)
#-----------------------------------------------------------------------

# Karte mit Statusanzeige aller BMS GPIO-Ausgaenge aufbauen (rot = 0, gruen = 1)
#-----------------------------------------------------------------------
def buildBmsOutputsCard ():
	groups = [
		html.Div(
			style={"minWidth": "220px", "marginRight": "32px", "marginBottom": "12px"},
			children=[
				html.P(title, style=_GROUP_TITLE_STYLE),
				*[_outputItem(field, label) for field, label in fields],
			],
		)
		for title, fields in _GROUPS
	]

	return html.Div(
		className="card",
		children=[
			html.P("BMS-Ausg\u00e4nge", className="card-sec"),
			html.Div(style={"display": "flex", "flexWrap": "wrap"}, children=groups),
		],
	)
#-----------------------------------------------------------------------
