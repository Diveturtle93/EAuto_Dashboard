import can
from dash import Input, Output, State
from dash.exceptions import PreventUpdate

from backend.can_bus import CanConfig

_BTN_CONNECT = {
    "fontSize": "12px", "padding": "6px 18px",
    "borderRadius": "5px", "cursor": "pointer", "fontWeight": "600",
    "border": "1px solid #f97316", "background": "#1f1108", "color": "#f97316",
}
_BTN_DISCONNECT = {
    "fontSize": "12px", "padding": "6px 18px",
    "borderRadius": "5px", "cursor": "pointer", "fontWeight": "600",
    "border": "1px solid #c0392b", "background": "#1a0a09", "color": "#e05a4a",
}


_FIELDS_VISIBLE = {"display": "flex", "alignItems": "center", "gap": "8px", "flexWrap": "wrap"}
_FIELDS_HIDDEN  = {"display": "none"}


def register_can_config_callback(app, can_manager, latest, lock):
    @app.callback(
        Output("btn_can_connect", "children"),
        Output("btn_can_connect", "style"),
        Output("can_connect_status", "children"),
        Output("can_connected", "data"),
        Output("can_config_fields", "style"),
        Input("btn_can_connect", "n_clicks"),
        State("can_interface", "value"),
        State("can_channel", "value"),
        State("can_bitrate", "value"),
        State("can_connected", "data"),
        prevent_initial_call=True,
    )
    def _toggle_can(n_clicks, interface, channel, bitrate, is_connected):
        if not n_clicks:
            raise PreventUpdate

        if is_connected:
            can_manager.stop()
            with lock:
                latest["last_rx_ms"] = 0
                latest["can_adapter_connected"] = False
            return "Verbinden", _BTN_CONNECT, "Getrennt.", False, _FIELDS_VISIBLE

        if not interface or not channel or not bitrate:
            return "Verbinden", _BTN_CONNECT, "Bitte Interface, Kanal und Baudrate auswählen.", False, _FIELDS_VISIBLE

        # Synchroner Verbindungstest – schlägt sofort fehl wenn kein Adapter vorhanden
        try:
            test_bus = can.Bus(interface=interface, channel=str(channel), bitrate=int(bitrate))
            test_bus.shutdown()
        except (can.CanError, OSError, ValueError) as e:
            return "Verbinden", _BTN_CONNECT, f"Kein Adapter gefunden: {e}", False, _FIELDS_VISIBLE

        config = CanConfig(interface, str(channel), int(bitrate))
        can_manager.start(config, latest, lock)
        return (
            "Trennen",
            _BTN_DISCONNECT,
            f"Verbunden: {interface} / {channel} @ {bitrate // 1000} kbit/s",
            True,
            _FIELDS_HIDDEN,
        )
