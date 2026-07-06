from dash import Input, Output

from ui.cards.bms_outputs_card import ALL_OUTPUT_FIELDS, DOT_STYLE

_ON_COLOR      = "var(--ok-alt)"
_OFF_COLOR     = "var(--err-strong)"
_UNKNOWN_COLOR = "var(--text-inactive)"


def register_bms_outputs_callback(app):

    @app.callback(
        [Output(f"bms_out_dot_{field}", "style") for field in ALL_OUTPUT_FIELDS],
        Input("snap", "data"),
        prevent_initial_call=True,
    )
    def _update_bms_outputs(snap):
        L = (snap or {}).get("L", {})
        styles = []
        for field in ALL_OUTPUT_FIELDS:
            val = L.get(field)
            if val == 1:
                color = _ON_COLOR
            elif val == 0:
                color = _OFF_COLOR
            else:
                color = _UNKNOWN_COLOR
            styles.append({**DOT_STYLE, "background": color})
        return styles
