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
    register_ecu_preset_callback,
    register_export_csv_callback,
    register_firmware_upload_callback,
    register_status_callback,
    register_temperature_chart_callback,
)
from ui.controls import build_time_window_controls, build_firmware_upload_card, build_can_config_fields

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
    can_adapter_connected=False,
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
    "background":   "#161922",
    "borderRadius": "10px",
    "boxShadow":    "0 1px 8px rgba(0,0,0,.40)",
    "border":       "1px solid #252836",
    "padding":      "12px 14px",
    "marginBottom": "14px",
}
_SEC = {
    "fontSize": "11px", "fontWeight": "700",
    "letterSpacing": "0.07em", "color": "#f97316",
    "textTransform": "uppercase", "marginBottom": "6px",
}
_TAB_STYLE = {
    "background": "#0d0f14", "color": "#9099a8",
    "border": "1px solid #252836", "padding": "6px 16px", "fontSize": "13px",
}
_TAB_SELECTED = {
    "background": "#161922", "color": "#f97316",
    "borderTop": "2px solid #f97316", "border": "1px solid #252836",
    "padding": "6px 16px", "fontSize": "13px",
}

# ═══════════════════════════════════════════════════════════════════════════════
#  Dashboard Layout
# ═══════════════════════════════════════════════════════════════════════════════
app = Dash(__name__)

app.layout = html.Div(
    style={"fontFamily": "'Inter', 'Segoe UI', sans-serif",
           "background": "#0d0f14", "minHeight": "100vh", "padding": "14px 24px",
           "maxWidth": "1300px", "margin": "0 auto", "color": "#f0f1f5"},
    children=[

        # ── Page title + CAN-Konfiguration ──────────────────────────────────────────────
        html.Div(
            style={**_CARD, "marginBottom": "14px", "padding": "10px 14px",
                   "display": "flex", "alignItems": "center",
                   "gap": "16px", "flexWrap": "wrap"},
            children=[
                html.H2("EAuto Live Dashboard",
                        style={"margin": "0", "fontSize": "16px", "color": "#f0f1f5",
                               "fontWeight": "700", "whiteSpace": "nowrap"}),
                html.Div(style={"flex": "1"}),
                build_can_config_fields(DEFAULT_INTERFACE, DEFAULT_CHANNEL, DEFAULT_BITRATE),
                html.Div(id="can_status_indicator"),
            ],
        ),

        # ── Tabs ──────────────────────────────────────────────────────────────────────
        dcc.Tabs(
            id="main_tabs",
            value="tab_dashboard",
            style={"marginBottom": "14px"},
            colors={"border": "#252836", "primary": "#f97316", "background": "#0d0f14"},
            children=[
                dcc.Tab(
                    label="Dashboard",
                    value="tab_dashboard",
                    style=_TAB_STYLE,
                    selected_style=_TAB_SELECTED,
                    children=[
                        html.Div(style={"paddingTop": "14px"}, children=[
                            build_time_window_controls(),
                            html.Div(id="status", style={"marginTop": "12px"}),
                            html.Div(style={**_CARD, "marginTop": "14px"}, children=[
                                html.Div("Temperatursensoren (ADC 0x538)", style=_SEC),
                                html.Div(id="temperature_chart"),
                            ]),
                        ]),
                    ],
                ),
                dcc.Tab(
                    label="Bootloader",
                    value="tab_bootloader",
                    style=_TAB_STYLE,
                    selected_style=_TAB_SELECTED,
                    children=[
                        html.Div(style={"paddingTop": "14px"}, children=[
                            build_firmware_upload_card(),
                        ]),
                    ],
                ),
            ],
        ),

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
register_ecu_preset_callback(app)
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
