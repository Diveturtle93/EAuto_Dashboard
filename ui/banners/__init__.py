def format_can_banner(snap):
    hidden = {"display": "none"}
    if snap is None:
        return "", hidden

    L = snap.get("L", {})
    pkt_age = (snap["now"] - L.get("last_rx_ms", 0) / 1000.0) if L.get("last_rx_ms") else 999.0
    if pkt_age < 3.0:
        return "", hidden

    msg = f"CAN connection lost -- no data for {pkt_age:.1f} s"
    style = {
        "background": "#c0392b",
        "color": "#fff",
        "padding": "10px 16px",
        "borderRadius": "8px",
        "fontWeight": "700",
        "fontSize": "14px",
        "marginBottom": "10px",
        "textAlign": "center",
        "boxShadow": "0 2px 8px rgba(192,57,43,0.35)",
    }
    return msg, style
