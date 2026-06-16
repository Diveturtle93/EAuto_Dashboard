from dash import Output, Input
from ui.banners import format_can_banner


def register_can_banner_callback(app):
    @app.callback(
        Output("can_banner", "children"),
        Output("can_banner", "style"),
        Input("snap", "data"),
    )
    def _update_can_banner(snap):
        return format_can_banner(snap)

    return _update_can_banner
