from dash import dcc, html


_CARD = {
    "background": "#ffffff",
    "borderRadius": "10px",
    "boxShadow": "0 1px 5px rgba(0,0,0,.10)",
    "padding": "12px 14px",
    "marginBottom": "14px",
}
_SEC = {
    "fontSize": "11px",
    "fontWeight": "700",
    "letterSpacing": "0.07em",
    "color": "#888",
    "textTransform": "uppercase",
    "marginBottom": "6px",
}
_LABEL = {
    "fontSize": "11px",
    "fontWeight": "700",
    "color": "#555",
    "marginBottom": "4px",
}
_INPUT = {
    "width": "100%",
    "padding": "7px 10px",
    "borderRadius": "6px",
    "border": "1px solid #d1d5db",
    "fontSize": "13px",
    "boxSizing": "border-box",
}

_INTERFACES = ["pcan", "vector", "kvaser", "slcan", "ixxat", "usb2can", "socketcan"]

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
_BITRATES = [
    {"label": "125 kbit/s",  "value": 125000},
    {"label": "250 kbit/s",  "value": 250000},
    {"label": "500 kbit/s",  "value": 500000},
    {"label": "1 Mbit/s",    "value": 1000000},
]

_BTN_CONNECT = {
    "fontSize": "12px", "padding": "6px 18px",
    "borderRadius": "5px", "cursor": "pointer", "fontWeight": "600",
    "border": "1px solid #27ae60", "background": "#eafaf1", "color": "#1e8449",
}
_BTN_DISCONNECT = {
    "fontSize": "12px", "padding": "6px 18px",
    "borderRadius": "5px", "cursor": "pointer", "fontWeight": "600",
    "border": "1px solid #c0392b", "background": "#fdf0ee", "color": "#c0392b",
}


def build_time_window_controls():
    """Build time window selection and export/reset buttons."""
    return html.Div(
        children=[
            html.Div(
                style={
                    **_CARD,
                    "marginBottom": "14px",
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "18px",
                    "flexWrap": "wrap",
                },
                children=[
                    html.P("Time Window", style={**_SEC, "marginBottom": "0"}),
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
                        inputStyle={"accentColor": "#2980b9", "cursor": "pointer"},
                        labelStyle={
                            "fontSize": "12px",
                            "color": "#444",
                            "cursor": "pointer",
                            "userSelect": "none",
                        },
                    ),
                    html.Button(
                        "Export CSV",
                        id="btn_csv",
                        style={
                            "fontSize": "11px",
                            "padding": "4px 12px",
                            "borderRadius": "5px",
                            "border": "1px solid #2980b9",
                            "background": "#eaf4fb",
                            "cursor": "pointer",
                            "color": "#2471a3",
                            "fontWeight": "600",
                            "marginLeft": "auto",
                        },
                    ),
                    html.Button(
                        "Reset",
                        id="btn_reset",
                        style={
                            "fontSize": "11px",
                            "padding": "4px 12px",
                            "borderRadius": "5px",
                            "border": "1px solid #c0392b",
                            "background": "#fdf0ee",
                            "cursor": "pointer",
                            "color": "#c0392b",
                            "fontWeight": "600",
                        },
                    ),
                ],
            ),
            html.P(
                "Tip: scroll to zoom on any graph. Double-click to reset.",
                style={"color": "#aaa", "fontSize": "11px", "marginTop": "4px"},
            ),
        ]
    )


def build_can_config_fields(default_interface="pcan", default_channel="PCAN_USBBUS1", default_bitrate=500000):
    """CAN-Adapter Konfigurationsfelder – kompakte Inline-Darstellung für die Titelleiste."""
    _INPUT_COMPACT = {**_INPUT, "padding": "5px 8px", "fontSize": "12px", "width": "130px"}
    return html.Div(
        style={"display": "flex", "alignItems": "center", "gap": "8px", "flexWrap": "wrap"},
        children=[
            html.Div(
                id="can_config_fields",
                style={"display": "flex", "alignItems": "center", "gap": "8px", "flexWrap": "wrap"},
                children=[
                    dcc.Dropdown(
                        id="can_interface",
                        options=[{"label": i, "value": i} for i in _INTERFACES],
                        value=default_interface,
                        clearable=False,
                        style={"fontSize": "12px", "width": "120px"},
                    ),
                    dcc.Input(
                        id="can_channel",
                        type="text",
                        value=default_channel,
                        debounce=True,
                        style=_INPUT_COMPACT,
                    ),
                    dcc.Dropdown(
                        id="can_bitrate",
                        options=_BITRATES,
                        value=default_bitrate,
                        clearable=False,
                        style={"fontSize": "12px", "width": "120px"},
                    ),
                ],
            ),
            html.Button(
                "Verbinden",
                id="btn_can_connect",
                n_clicks=0,
                style=_BTN_CONNECT,
            ),
            html.Div(id="can_connect_status", style={"fontSize": "12px", "color": "#555"}),
            dcc.Store(id="can_connected", data=False),
        ],
    )


def build_firmware_upload_card():
    """Build firmware upload card with bootloader configuration."""
    return html.Div(
        style={**_CARD, "background": "#fcfcff", "border": "1px solid #dfe3ea"},
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
                    "borderColor": "#95a5a6",
                    "backgroundColor": "#fafafa",
                    "textAlign": "center",
                    "color": "#333",
                    "cursor": "pointer",
                    "overflow": "hidden",
                },
                multiple=False,
            ),
            html.Div(
                style={
                    "background": "#f0f4ff",
                    "border": "1px solid #c7d2fe",
                    "borderRadius": "8px",
                    "padding": "14px 16px",
                    "marginTop": "12px",
                    "fontSize": "12px",
                    "color": "#374151",
                    "lineHeight": "1.7",
                },
                children=[
                    html.P(
                        "So wird ein Update durchgeführt:",
                        style={"fontWeight": "700", "margin": "0 0 6px 0", "fontSize": "12px"},
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
                        style={"fontWeight": "700", "margin": "0 0 4px 0", "fontSize": "12px"},
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
                                "color": "#555",
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
                                "border": "1px solid #d1d5db",
                            },
                        ),
                    ]),
                    html.Div(children=[
                        html.Div(
                            "Bootloader TX CAN-ID",
                            style={
                                "fontSize": "11px",
                                "fontWeight": "700",
                                "color": "#555",
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
                                "border": "1px solid #d1d5db",
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
