# Layout-Bausteine für die Titelleiste des Dashboards: Theme-Umschalter,
# CAN-Adapter-Konfigurationsfelder (Interface/Kanal/Bitrate + Verbinden-Button)
# sowie die CAN-Status-Pille. Die zugehörige Logik liegt in
# ui/callbacks/theme.py bzw. ui/callbacks/can_config.py.

from dash import dcc, html

_INPUT = {
    "width": "100%",
    "padding": "7px 10px",
    "borderRadius": "6px",
    "border": "1px solid var(--border)",
    "background": "var(--bg-page)",
    "color": "var(--text)",
    "fontSize": "13px",
    "boxSizing": "border-box",
}

_INTERFACES = ["pcan", "vector", "kvaser", "slcan", "ixxat", "usb2can", "socketcan"]

_BITRATES = [
    {"label": "125 kbit/s",  "value": 125000},
    {"label": "250 kbit/s",  "value": 250000},
    {"label": "500 kbit/s",  "value": 500000},
    {"label": "1 Mbit/s",    "value": 1000000},
]

def build_theme_button():
    """Theme-Toggle-Button; Aufschrift zeigt wohin der nächste Klick wechselt."""
    return html.Button(
        "Dunkel",
        id="theme-btn",
        n_clicks=0,
        className="btn",
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
                className="btn",
            ),
            html.Div(id="can_connect_status", style={"fontSize": "12px", "color": "var(--text-secondary)"}),
            dcc.Store(id="can_connected", data=False),
        ],
    )


def format_can_status(snap, is_connected):
    """Returns the CAN status pill for the header (4 states: grey/yellow/green/red).

    snap erwartet ein Dict mit "L" (latest-Snapshot) und "now" (aktueller
    Zeitstempel); is_connected gibt an, ob der CanManager aktuell einen
    laufenden Empfangs-Thread besitzt.
    """
    if not is_connected:
        # Grau: kein CAN-Adapter konfiguriert/verbunden
        return _pill("Kein Adapter", "var(--bg-subtle)", "var(--text-inactive)", "var(--text-muted)")

    L = snap.get("L", {}) if snap else {}
    if not L.get("can_adapter_connected", False):
        # Gelb: Adapter wurde nach Verbindungsaufbau getrennt (Reconnect läuft)
        return _pill("Adapter getrennt", "var(--warn-bg)", "var(--warn)", "var(--warn)")

    last_rx = L.get("last_rx_ms", 0)
    if last_rx == 0:
        # Grün: verbunden, aber noch keine Nachricht empfangen
        return _pill("CAN OK", "var(--ok-alt-bg)", "var(--ok-alt)", "var(--ok-alt)")

    pkt_age = snap["now"] - last_rx / 1000.0
    if pkt_age < 3.0:
        # Grün: zuletzt empfangener Frame ist noch frisch
        return _pill("CAN OK", "var(--ok-alt-bg)", "var(--ok-alt)", "var(--ok-alt)")

    # Rot: seit > 3 s keine CAN-Nachricht mehr empfangen
    return _pill(f"CAN Fehler ({pkt_age:.0f} s)", "var(--err-bg)", "var(--err-strong)", "var(--err-text)")


def _pill(text, bg, dot, text_color):
    """Baut die kleine, farbige Status-Pille (Punkt + Text)."""
    return html.Div(
        children=[
            html.Span(style={
                "display": "inline-block", "width": "8px", "height": "8px",
                "borderRadius": "50%", "background": dot,
                "marginRight": "6px", "flexShrink": "0",
            }),
            html.Span(text, style={"fontSize": "12px", "fontWeight": "600", "color": text_color}),
        ],
        style={
            "display": "inline-flex", "alignItems": "center",
            "padding": "5px 12px", "borderRadius": "20px",
            "background": bg, "border": f"1px solid {dot}",
            "whiteSpace": "nowrap",
        },
    )
