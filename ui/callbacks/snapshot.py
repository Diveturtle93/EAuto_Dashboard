from dash import Output, Input
import time


def register_snapshot_callback(app, lock, latest):
    @app.callback(
        Output("snap", "data"),
        Input("tick", "n_intervals"),
    )
    def _snapshot(_):
        with lock:
            L = latest.copy()
        return dict(
            L=L,
            now=time.time(),
            mono_now=time.monotonic(),
        )

    return _snapshot
