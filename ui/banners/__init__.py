from dash import html


def format_can_status(snap, is_connected):
    """Returns the CAN status pill for the header (3 states: white/green/red)."""
    if not is_connected:
        return _pill("Kein Adapter", "#f0f0f0", "#bbb", "#888")

    if snap is None:
        return _pill("CAN OK", "#eafaf1", "#27ae60", "#1e8449")

    L = snap.get("L", {})
    last_rx = L.get("last_rx_ms", 0)

    if last_rx == 0:
        return _pill("CAN OK", "#eafaf1", "#27ae60", "#1e8449")

    pkt_age = snap["now"] - last_rx / 1000.0
    if pkt_age < 3.0:
        return _pill("CAN OK", "#eafaf1", "#27ae60", "#1e8449")

    return _pill(f"CAN Fehler ({pkt_age:.0f} s)", "#fdf0ee", "#c0392b", "#c0392b")


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
