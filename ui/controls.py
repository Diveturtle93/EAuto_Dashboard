from dash import dcc, html


_CARD = {
    "background": "#ffffff",
    "borderRadius": "10px",
    "boxShadow": "0 1px 5px rgba(0,0,0,.10)",
    "padding": "12px 14px",
    "marginBottom": "14px",
}
_SEC = {
    "fontSize": "11px",
    "fontWeight": "700",
    "letterSpacing": "0.07em",
    "color": "#888",
    "textTransform": "uppercase",
    "marginBottom": "6px",
}


def build_time_window_controls():
    """Build time window selection and export/reset buttons."""
    return html.Div(
        children=[
            html.Div(
                style={
                    **_CARD,
                    "marginBottom": "14px",
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "18px",
                    "flexWrap": "wrap",
                },
                children=[
                    html.P("Time Window", style={**_SEC, "marginBottom": "0"}),
                    dcc.RadioItems(
                        id="win_sel",
                        options=[
                            {"label": "  1 min", "value": 60},
                            {"label": "  5 min", "value": 300},
                            {"label": "  30 min", "value": 1800},
                            {"label": "  All", "value": 0},
                        ],
                        value=0,
                        inline=True,
                        inputStyle={"accentColor": "#2980b9", "cursor": "pointer"},
                        labelStyle={
                            "fontSize": "12px",
                            "color": "#444",
                            "cursor": "pointer",
                            "userSelect": "none",
                        },
                    ),
                    html.Button(
                        "Export CSV",
                        id="btn_csv",
                        style={
                            "fontSize": "11px",
                            "padding": "4px 12px",
                            "borderRadius": "5px",
                            "border": "1px solid #2980b9",
                            "background": "#eaf4fb",
                            "cursor": "pointer",
                            "color": "#2471a3",
                            "fontWeight": "600",
                            "marginLeft": "auto",
                        },
                    ),
                    html.Button(
                        "Reset",
                        id="btn_reset",
                        style={
                            "fontSize": "11px",
                            "padding": "4px 12px",
                            "borderRadius": "5px",
                            "border": "1px solid #c0392b",
                            "background": "#fdf0ee",
                            "cursor": "pointer",
                            "color": "#c0392b",
                            "fontWeight": "600",
                        },
                    ),
                ],
            ),
            html.P(
                "Tip: scroll to zoom on any graph. Double-click to reset.",
                style={"color": "#aaa", "fontSize": "11px", "marginTop": "4px"},
            ),
        ]
    )


def build_firmware_upload_card():
    """Build firmware upload card with bootloader configuration."""
    return html.Div(
        style={**_CARD, "background": "#fcfcff", "border": "1px solid #dfe3ea"},
        children=[
            html.P("Firmware Update", style={**_SEC, "marginBottom": "8px"}),
            dcc.Upload(
                id="firmware_upload",
                children=html.Div([
                    "Firmware-Datei hierhin ziehen oder klicken, um sie auszuwählen."
                ]),
                style={
                    "width": "100%",
                    "maxWidth": "100%",
                    "boxSizing": "border-box",
                    "margin": "0 auto",
                    "padding": "16px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "10px",
                    "borderColor": "#95a5a6",
                    "backgroundColor": "#fafafa",
                    "textAlign": "center",
                    "color": "#333",
                    "cursor": "pointer",
                    "overflow": "hidden",
                },
                multiple=False,
            ),
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))",
                    "gap": "12px",
                    "marginTop": "16px",
                },
                children=[
                    html.Div(children=[
                        html.Div(
                            "Bootloader RX CAN-ID",
                            style={
                                "fontSize": "11px",
                                "fontWeight": "700",
                                "color": "#555",
                                "marginBottom": "4px",
                            },
                        ),
                        dcc.Input(
                            id="bootloader_rx_id",
                            type="text",
                            value="0x66E",
                            style={
                                "width": "100%",
                                "padding": "8px 10px",
                                "borderRadius": "6px",
                                "border": "1px solid #d1d5db",
                            },
                        ),
                    ]),
                    html.Div(children=[
                        html.Div(
                            "Bootloader TX CAN-ID",
                            style={
                                "fontSize": "11px",
                                "fontWeight": "700",
                                "color": "#555",
                                "marginBottom": "4px",
                            },
                        ),
                        dcc.Input(
                            id="bootloader_tx_id",
                            type="text",
                            value="0x7EE",
                            style={
                                "width": "100%",
                                "padding": "8px 10px",
                                "borderRadius": "6px",
                                "border": "1px solid #d1d5db",
                            },
                        ),
                    ]),
                    html.Div(children=[
                        html.Div(
                            "Program Startadresse",
                            style={
                                "fontSize": "11px",
                                "fontWeight": "700",
                                "color": "#555",
                                "marginBottom": "4px",
                            },
                        ),
                        dcc.Input(
                            id="bootloader_start_address",
                            type="text",
                            value="0x08003000",
                            style={
                                "width": "100%",
                                "padding": "8px 10px",
                                "borderRadius": "6px",
                                "border": "1px solid #d1d5db",
                            },
                        ),
                    ]),
                ],
            ),
            dcc.Loading(
                id="bootloader_loading",
                type="dot",
                children=html.Div(id="bootloader_status", style={"marginTop": "12px", "fontSize": "13px"}),
                style={"width": "100%", "paddingTop": "8px"},
            ),
        ],
    )
