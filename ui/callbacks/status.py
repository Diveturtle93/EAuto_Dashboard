from dash import Output, Input, html


STATUS_NAME = {
    0: "Start",
    1: "Ready",
    2: "KL15",
    3: "Anlassen",
    4: "Precharge",
    5: "ReadyToDrive",
    6: "Drive",
    7: "Standby",
    8: "Ausschalten",
    9: "Laden",
}

COLOR_MAP = {
    "Normal": "#2ecc71",       # green
    "Warning": "#f1c40f",      # yellow
    "Error": "#e74c3c",        # red
    "Critical Error": "#8e44ad", # purple
    "Invalid": "#95a5a6",      # grey
    "Severe Error": "#c0392b", # strong red
    "Unknown": "#7f8c8d",
}


def register_status_callback(app):
    def make_field(label, value, background="#161922", color="#f0f1f5"):
        return html.Div(
            children=[
                html.Div(label, style={"fontSize": "12px", "fontWeight": "700", "marginBottom": "6px", "color": "#9099a8"}),
                html.Div(value, style={
                    "background": background,
                    "color": color,
                    "padding": "12px",
                    "borderRadius": "8px",
                    "textAlign": "center",
                    "fontWeight": "700",
                }),
            ],
            style={"minWidth": "140px"},
        )

    @app.callback(
        Output("status", "children"),
        Input("snap", "data"),
    )
    def _status(snap):
        if snap is None:
            return ""
        L = snap.get("L", {})

        bms_state = L.get("bms_state", "Unknown")
        bms_status_code = L.get("bms_status_code")
        motor_state = L.get("motor_state", "Unknown")
        motor_status_code = L.get("motor_status_code")

        if isinstance(bms_status_code, int):
            bms_status_text = f"{bms_status_code} — {STATUS_NAME.get(bms_status_code, str(bms_status_code))}"
        else:
            bms_status_text = "--"

        if isinstance(motor_status_code, int):
            motor_status_text = f"{motor_status_code} — {STATUS_NAME.get(motor_status_code, str(motor_status_code))}"
        else:
            motor_status_text = "--"

        items = [
            make_field("BMS Zustand", bms_state, background=COLOR_MAP.get(bms_state, "#7f8c8d"), color="#fff"),
            make_field("BMS Status", bms_status_text),
            make_field("Motorzustand", motor_state, background=COLOR_MAP.get(motor_state, "#7f8c8d"), color="#fff"),
            make_field("Motorstatus", motor_status_text),
        ]

        return html.Div(items, style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "12px"})

    return _status
