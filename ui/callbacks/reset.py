from dash import Output, Input


def register_reset_callback(app, lock, latest):
    @app.callback(
        Output("reset_dummy", "children"),
        Input("btn_reset", "n_clicks"),
        prevent_initial_call=True,
    )
    def _reset_data(_):
        with lock:
            latest["last_rx_ms"] = 0
        return ""

    return _reset_data
