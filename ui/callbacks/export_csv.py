import csv
import io
from datetime import datetime

from dash import Output, Input, State, dcc


def register_export_csv_callback(app):
    @app.callback(
        Output("dl", "data"),
        Input("btn_csv", "n_clicks"),
        State("snap", "data"),
        prevent_initial_call=True,
    )
    def _export_csv(_n, snap):
        if snap is None:
            return None

        buf = io.StringIO()
        writer = csv.writer(buf)

        L = snap.get("L", snap)
        writer.writerow(["key", "value"])
        for k, v in L.items():
            val = ";".join(map(str, v)) if isinstance(v, (list, tuple)) else str(v)
            writer.writerow([k, val])

        fname = f"EAuto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return dcc.send_string(buf.getvalue(), filename=fname)

    return _export_csv
