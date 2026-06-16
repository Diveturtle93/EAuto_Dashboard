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

        if snap.get("ts"):
            # Legacy time-series format: snap contains 'ts' + value lists
            keys = ["soc", "u_v", "i_a", "power",
                    "chg_batt_v", "chg_i", "chg_cmd_v", "chg_cmd_i",
                    "thrust_pct", "thrust_f_pct"]
            writer.writerow(["time_s"] + keys)
            for i, t in enumerate(snap["ts"]):
                row = [f"{t:.2f}"]
                for k in keys:
                    s = snap.get(k, [])
                    row.append(f"{s[i]:.4f}" if i < len(s) else "")
                writer.writerow(row)
        else:
            # Current snapshot format: snap contains 'L' (latest dict)
            L = snap.get("L", snap)
            writer.writerow(["key", "value"])
            for k, v in L.items():
                val = ";".join(map(str, v)) if isinstance(v, (list, tuple)) else str(v)
                writer.writerow([k, val])

        fname = f"EAuto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return dcc.send_string(buf.getvalue(), filename=fname)

    return _export_csv
