from dash import Input, Output
from dash.exceptions import PreventUpdate


def register_ecu_preset_callback(app):
    @app.callback(
        Output("bootloader_rx_id", "value"),
        Output("bootloader_tx_id", "value"),
        Input("ecu_preset", "value"),
        prevent_initial_call=True,
    )
    def _apply_preset(preset):
        if not preset:
            raise PreventUpdate
        rx, tx = preset.split("|")
        return rx, tx
