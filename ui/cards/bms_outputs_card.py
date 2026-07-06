# Karte mit Statusanzeige aller BMS GPIO-Ausgänge (CAN 0x237). Jeder Ausgang
# wird als farbiger Punkt dargestellt: Rot = 0 (aus), Grün = 1 (an). Wird per
# Callback (ui/callbacks/bms_outputs.py) bei jedem neuen Snapshot aktualisiert.

from dash import html

# (Gruppentitel, [(Feldname aus can_0x237.py, Anzeigename), ...])
_GROUPS = [
    ("System", [
        ("sys_ams_limit",    "BMS Error"),
        ("sys_imd_ok",       "IMD Error"),
        ("sys_ams_ok",       "AMS-OK"),
        ("sys_freigabe",     "Freigabe RUN (Bamocar)"),
        ("sys_recuperation", "Recuperation möglich"),
        ("sys_hv_p",         "HV-Relais Positiv"),
        ("sys_hv_n",         "HV-Relais Negativ"),
        ("sys_power_on",     "Power ON"),
    ]),
    ("Highcurrent", [
        ("hc_digital1",      "Digitaler Ausgang 1"),
        ("hc_digital2",      "Digitaler Ausgang 2"),
        ("hc_precharge_out", "Precharge Relais"),
        ("hc_hv_m",          "HV-Relais Zusätzlich"),
        ("hc_hv_chg",        "HV-Relais Ladegerät"),
        ("hc_heater1",       "Heizung 1"),
        ("hc_heater2",       "Heizung 2"),
    ]),
    ("LED", [
        ("led_inlet_red",   "Inlet LED Rot"),
        ("led_inlet_green", "Inlet LED Grün"),
        ("led_akku_error",  "Akku Error LED"),
        ("led_red",         "PCB LED Rot"),
        ("led_green",       "PCB LED Grün"),
        ("led_blue",        "PCB LED Blau"),
    ]),
    ("Komfort", [
        ("komfort_trigger_out", "Trigger Stromsensor"),
        ("komfort_isospi_en",   "IsoSPI Spannung"),
        ("komfort_isohv_en",    "Precharge Abfrage"),
    ]),
]

# Alle Feldnamen in fester Reihenfolge, für den Callback (ein Output-Dot je Feld)
ALL_OUTPUT_FIELDS = [field for _, fields in _GROUPS for field, _ in fields]

DOT_STYLE = {
    "display": "inline-block", "width": "10px", "height": "10px",
    "borderRadius": "50%", "marginRight": "8px", "flexShrink": "0",
    "background": "var(--text-inactive)",
}

_ITEM_STYLE = {
    "display": "flex", "alignItems": "center",
    "padding": "4px 0", "fontSize": "12px", "color": "var(--text-secondary)",
}

_GROUP_TITLE_STYLE = {
    "fontSize": "12px", "fontWeight": "700", "color": "var(--text-muted)",
    "margin": "0 0 6px 0", "textTransform": "uppercase", "letterSpacing": "0.03em",
}


def _output_item(field, label):
    return html.Div(
        style=_ITEM_STYLE,
        children=[
            html.Span(style=DOT_STYLE, id=f"bms_out_dot_{field}"),
            html.Span(label),
        ],
    )


def build_bms_outputs_card():
    """Karte mit Statusanzeige aller BMS GPIO-Ausgänge (rot = 0, grün = 1)."""
    groups = [
        html.Div(
            style={"minWidth": "220px", "marginRight": "32px", "marginBottom": "12px"},
            children=[
                html.P(title, style=_GROUP_TITLE_STYLE),
                *[_output_item(field, label) for field, label in fields],
            ],
        )
        for title, fields in _GROUPS
    ]

    return html.Div(
        className="card",
        children=[
            html.P("BMS-Ausgänge", className="card-sec"),
            html.Div(style={"display": "flex", "flexWrap": "wrap"}, children=groups),
        ],
    )
