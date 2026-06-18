"""
EAuto Live Dashboard  –  eauto_dashboard.py
Windows-compatible version using python-can for CAN interface support.
Supports PCAN, Vector, Kvaser, and other Windows CAN adapters.

Install dependencies:
  pip install dash plotly python-can

Run:
  python eauto_dashboard.py [interface] [channel] [bitrate]
  # The arguments pre-fill the CAN config card in the browser; the adapter
  # is connected only after clicking "Verbinden" in the UI.
  # examples:
  #   python eauto_dashboard.py pcan PCAN_USBBUS1 500000
  #   python eauto_dashboard.py vector 0 500000
  #   python eauto_dashboard.py slcan COM3 500000
  open http://localhost:8052
"""

import sys
import threading

from dash import Dash, dcc, html

from backend.can_bus import can_manager
from ui.callbacks import (
    register_snapshot_callback,
    register_reset_callback,
    register_can_banner_callback,
    register_can_config_callback,
    register_export_csv_callback,
    register_firmware_upload_callback,
    register_status_callback,
    register_temperature_chart_callback,
)
from ui.controls import build_time_window_controls, build_firmware_upload_card, build_can_config_card
from ui.callbacks.temperature_chart import build_temperature_graph

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG  (command-line args → pre-fill UI defaults only, no auto-connect)
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_INTERFACE = sys.argv[1] if len(sys.argv) > 1 else "pcan"
DEFAULT_CHANNEL   = sys.argv[2] if len(sys.argv) > 2 else "PCAN_USBBUS1"
DEFAULT_BITRATE   = int(sys.argv[3]) if len(sys.argv) > 3 else 500000
INTERVAL          = 500         # ms dashboard refresh

# ═══════════════════════════════════════════════════════════════════════════════
#  DATA STORE
# ═══════════════════════════════════════════════════════════════════════════════
lock   = threading.Lock()

# ── latest snapshot (all fields) ────────────────────────────────────────────
latest = dict(
    last_rx_ms=0,
    bms_status_code=None,
    bms_state="Unknown",
    motor_status_code=None,
    motor_state="Unknown",
    temp_adc_1=None,
    temp_adc_2=None,
    temp_adc_3=None,
    temp_adc_4=None,
)
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
#  LAYOUT BUILDING BLOCKS
# ═══════════════════════════════════════════════════════════════════════════════
_CARD = {
    "background":  "#ffffff",
    "borderRadius": "10px",
    "boxShadow":   "0 1px 5px rgba(0,0,0,.10)",
    "padding":     "12px 14px",
    "marginBottom": "14px",
}
_SEC = {
    "fontSize": "11px", "fontWeight": "700",
    "letterSpacing": "0.07em", "color": "#888",
    "textTransform": "uppercase", "marginBottom": "6px",
}

# ═══════════════════════════════════════════════════════════════════════════════
#  Dashboard Layout
# ═══════════════════════════════════════════════════════════════════════════════
app = Dash(__name__)
app.layout = html.Div(
    style={"fontFamily": "'Inter', 'Segoe UI', sans-serif",
           "background": "#eef0f4", "minHeight": "100vh", "padding": "14px 24px",
           "maxWidth": "1300px", "margin": "0 auto"},
    children=[

        # ── Page title ──────────────────────────────────────────────────────────────────
        html.Div(
            style={**_CARD, "marginBottom": "14px", "display": "flex",
                   "alignItems": "center", "justifyContent": "space-between",
                   "flexWrap": "wrap", "gap": "10px"},
            children=[
                html.Div([
                    html.H2("EAuto Live Dashboard (Windows)",
                            style={"margin": "0", "fontSize": "20px", "color": "#222",
                                   "fontWeight": "700"}),
                    html.Span("CAN-Adapter wird über das Konfigurationsfeld unten verbunden.",
                              style={"fontSize": "11px", "color": "#888"}),
                ]),
                html.Div(id="can_status_indicator"),
            ],
        ),

        # ── CAN-Adapter Konfiguration ──────────────────────────────────────────────────
        build_can_config_card(DEFAULT_INTERFACE, DEFAULT_CHANNEL, DEFAULT_BITRATE),

        # ── Main Grid: Dashboard Controls ─────────────────────────────────────────────
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr", "gap": "14px"},
            children=[
                build_time_window_controls(),
                build_firmware_upload_card(),
            ]
        ),

        html.Div(id="status", style={"marginTop": "12px"}),

        # ── Temperatursensoren Balkendiagramm ─────────────────────────────────────────
        html.Div(style={**_CARD, "marginTop": "14px"}, children=[
            html.Div("Temperatursensoren (ADC 0x538)", style=_SEC),
            build_temperature_graph(),
        ]),
        dcc.Interval(id="tick", interval=INTERVAL, n_intervals=0),
        dcc.Store(id="snap", storage_type="memory"),
        dcc.Download(id="dl"),
        html.Div(id="reset_dummy", style={"display": "none"}),
    ],
)
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
#  SNAPSHOT / CALLBACK REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════════
register_snapshot_callback(app, lock, latest)
register_reset_callback(app, lock, latest)
register_can_banner_callback(app)
register_can_config_callback(app, can_manager, latest, lock)
register_export_csv_callback(app)
register_firmware_upload_callback(app, can_manager, latest, lock)
register_status_callback(app)
register_temperature_chart_callback(app)
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
#  Hauptprogramm starten
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  EAuto Live Dashboard (Windows)")
    print(f"  Standardwerte: {DEFAULT_INTERFACE} / {DEFAULT_CHANNEL} @ {DEFAULT_BITRATE} bps")
    print(f"  CAN-Adapter bitte im Browser verbinden.")
    print(f"  Dashboard: http://localhost:8052")
    print("=" * 60)
    app.run(host="127.0.0.1", port=8052, debug=False)
# ═══════════════════════════════════════════════════════════════════════════════
