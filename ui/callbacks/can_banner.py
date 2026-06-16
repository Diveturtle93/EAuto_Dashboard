from dash import Output, Input
from ui.banners import format_can_status


def register_can_banner_callback(app):
    @app.callback(
        Output("can_status_indicator", "children"),
        Input("snap", "data"),
        Input("can_connected", "data"),
    )
    def _update_can_status(snap, is_connected):
        return format_can_status(snap, is_connected)

    return _update_can_status
