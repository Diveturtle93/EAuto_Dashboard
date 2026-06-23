from dash import html


def format_can_status(snap, is_connected):
    """Returns the CAN status pill for the header (4 states: grey/yellow/green/red)."""
    if not is_connected:
        return _pill("Kein Adapter", "#1a1d27", "#4a5060", "#6b7280")

    L = snap.get("L", {}) if snap else {}
    if not L.get("can_adapter_connected", False):
        # Adapter wurde nach Verbindungsaufbau getrennt (Reconnect läuft)
        return _pill("Adapter getrennt", "#1f1808", "#e6a817", "#f0b429")

    last_rx = L.get("last_rx_ms", 0)
    if last_rx == 0:
        return _pill("CAN OK", "#0a1f14", "#27ae60", "#2ecc71")

    pkt_age = snap["now"] - last_rx / 1000.0
    if pkt_age < 3.0:
        return _pill("CAN OK", "#0a1f14", "#27ae60", "#2ecc71")

    return _pill(f"CAN Fehler ({pkt_age:.0f} s)", "#1f0a09", "#c0392b", "#e05a4a")


def _pill(text, bg, dot, text_color):
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
