from dash import dcc, html

_CARD = {
    "background": "var(--bg-card)",
    "borderRadius": "10px",
    "boxShadow": "0 1px 8px var(--shadow-card)",
    "border": "1px solid var(--border)",
    "padding": "12px 14px",
    "marginBottom": "14px",
}
_SEC = {
    "fontSize": "11px",
    "fontWeight": "700",
    "letterSpacing": "0.07em",
    "color": "var(--accent)",
    "textTransform": "uppercase",
    "marginBottom": "6px",
}
_LABEL = {
    "fontSize": "11px",
    "fontWeight": "700",
    "color": "var(--text-secondary)",
    "marginBottom": "4px",
}

# (Name, Bootloader-RX-ID, Bootloader-TX-ID)
ECU_PRESETS = [
    ("BMS",         "0x7E0", "0x7E1"),
    ("Charger",     "0x66A", "0x7E4"),
    ("HBT",         "0x66B", "0x7E5"),
    ("MBT",         "0x66C", "0x7E6"),
    ("SOC Display", "0x66D", "0x7E7"),
    ("Display 1",   "0x66E", "0x7EE"),
    ("Display 2",   "0x66F", "0x7EF"),
]


def build_firmware_upload_card():
    return html.Div(
        style={**_CARD},
        children=[
            html.P("Firmware Update", style={**_SEC, "marginBottom": "8px"}),
            dcc.Upload(
                id="firmware_upload",
                children=html.Div([
                    "Firmware-Datei hierhin ziehen oder klicken, um sie auszuwählen."
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
                        "So wird ein Update durchgeführt:",
                        style={"fontWeight": "700", "margin": "0 0 6px 0", "fontSize": "12px", "color": "var(--text)"},
                    ),
                    html.Ol(
                        children=[
                            html.Li("Firmware-Datei (.srec) oben in das Upload-Feld ziehen oder per Klick auswählen."),
                            html.Li("Das Steuergerät wechselt automatisch in den Bootloader-Modus, sobald es die erste Bootloader-Nachricht empfängt – ein manueller Reset oder Power-Cycle ist nicht erforderlich."),
                            html.Li("Der Upload startet automatisch, sobald der Bootloader erkannt wird (Wartezeit bis zu 30 s)."),
                            html.Li("Den Fortschritt und etwaige Fehlermeldungen im Statusbereich unterhalb der Schaltfläche verfolgen."),
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
                                " CAN-ID, über die das Dashboard Befehle an den Bootloader im Steuergerät sendet. "
                                "Muss mit der im Steuergerät konfigurierten Master-TX-ID übereinstimmen.",
                            ]),
                            html.Li([
                                html.Strong("Bootloader TX CAN-ID:"),
                                " CAN-ID, über die der Bootloader Antworten an das Dashboard zurücksendet. "
                                "Muss mit der im Steuergerät konfigurierten Master-RX-ID übereinstimmen.",
                            ]),
                        ],
                        style={"margin": "0", "paddingLeft": "18px"},
                    ),
                ],
            ),
            html.Div(
                style={"marginTop": "16px"},
                children=[
                    html.Div("Steuergerät", style=_LABEL),
                    dcc.Dropdown(
                        id="ecu_preset",
                        options=(
                            [{"label": "– Manuell –", "value": ""}]
                            + [
                                {"label": f"{name}  ({rx} / {tx})", "value": f"{rx}|{tx}"}
                                for name, rx, tx in ECU_PRESETS
                            ]
                        ),
                        value="",
                        clearable=False,
                        placeholder="Steuergerät wählen …",
                        style={"fontSize": "13px"},
                    ),
                ],
            ),
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
