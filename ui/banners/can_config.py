from dash import dcc, html

_INTERFACES = ["pcan", "vector", "kvaser", "slcan", "ixxat", "usb2can", "socketcan"]

_BITRATES = [
    {"label": "125 kbit/s",  "value": 125000},
    {"label": "250 kbit/s",  "value": 250000},
    {"label": "500 kbit/s",  "value": 500000},
    {"label": "1 Mbit/s",    "value": 1000000},
]

_INPUT_COMPACT = {
    "padding": "5px 8px", "fontSize": "12px", "width": "130px",
    "borderRadius": "6px", "border": "1px solid var(--border)",
    "background": "var(--bg-page)", "color": "var(--text)", "boxSizing": "border-box",
}


def build_can_config_fields(default_interface="pcan", default_channel="PCAN_USBBUS1", default_bitrate=500000):
    """CAN-Adapter Konfigurationsfelder – kompakte Inline-Darstellung für die Titelleiste."""
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
                className="btn",
            ),
            html.Div(id="can_connect_status", style={"fontSize": "12px", "color": "var(--text-secondary)"}),
            dcc.Store(id="can_connected", data=False),
        ],
    )
