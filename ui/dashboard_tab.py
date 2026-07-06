from dash import dcc, html


def build_time_window_controls():
    """Build time window selection and export/reset buttons."""
    return html.Div(
        children=[
            html.Div(
                className="card",
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "18px",
                    "flexWrap": "wrap",
                },
                children=[
                    html.P("Time Window", className="card-sec", style={"marginBottom": "0"}),
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
                        inputStyle={"accentColor": "var(--accent)", "cursor": "pointer"},
                        labelStyle={
                            "fontSize": "12px",
                            "color": "var(--text-secondary)",
                            "cursor": "pointer",
                            "userSelect": "none",
                        },
                    ),
                    html.Button(
                        "Export CSV",
                        id="btn_csv",
                        className="btn",
                        style={"marginLeft": "auto"},
                    ),
                    html.Button(
                        "Reset",
                        id="btn_reset",
                        className="btn-danger",
                    ),
                ],
            ),
            html.P(
                "Tip: scroll to zoom on any graph. Double-click to reset.",
                style={"color": "var(--text-muted)", "fontSize": "11px", "marginTop": "4px"},
            ),
        ]
    )
