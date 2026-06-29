import plotly.graph_objects as go
from dash import dcc, html

_NUM_MODULES = 10
_CELLS       = 12
_SENSORS     = 16

_CARD = {
    "background":   "var(--bg-card)",
    "borderRadius": "10px",
    "boxShadow":    "0 1px 8px var(--shadow-card)",
    "border":       "1px solid var(--border)",
    "padding":      "12px 14px",
    "marginBottom": "14px",
}
_SEC = {
    "fontSize": "11px", "fontWeight": "700", "letterSpacing": "0.07em",
    "color": "var(--accent)", "textTransform": "uppercase", "marginBottom": "8px",
}
_STAT_STYLE = {
    "display": "inline-block", "marginRight": "24px",
    "fontSize": "12px", "color": "var(--text-secondary)",
}
_STAT_VAL = {"fontWeight": "700", "color": "var(--text)"}

_BAR_LAYOUT = dict(
    margin=dict(t=10, b=85, l=60, r=20),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(size=11),
    showlegend=False,
    bargap=0.08,
    xaxis=dict(tickangle=-90, tickfont=dict(size=8)),
)

# One distinct color per module, repeated for each cell/sensor in that module
_MOD_COLORS = [
    "#4C9BE8", "#E86B4C", "#4CE87A", "#E8C84C", "#9B4CE8",
    "#4CE8D8", "#E84C9B", "#8CE84C", "#E8A04C", "#4C4CE8",
]

_V_XLABELS = [f"M{m+1}-Z{c+1}" for m in range(_NUM_MODULES) for c in range(_CELLS)]
_V_COLORS  = [_MOD_COLORS[m] for m in range(_NUM_MODULES) for _ in range(_CELLS)]

_T_XLABELS = [f"M{m+1}-S{s+1}" for m in range(_NUM_MODULES) for s in range(_SENSORS)]
_T_COLORS  = [_MOD_COLORS[m] for m in range(_NUM_MODULES) for _ in range(_SENSORS)]


def build_cell_data_tab():
    """Build the complete 'Zellen' tab content."""

    # ── Voltage bar chart ────────────────────────────────────────────────────
    v_fig = go.Figure(go.Bar(
        x=_V_XLABELS,
        y=[None] * (_NUM_MODULES * _CELLS),
        marker=dict(color=_V_COLORS),
        hovertemplate="%{x}<br><b>%{y} mV</b><extra></extra>",
    ))
    v_fig.update_layout(
        **_BAR_LAYOUT,
        height=320,
        yaxis=dict(title=dict(text="mV", standoff=4)),
    )

    # ── Temperature bar chart ────────────────────────────────────────────────
    t_fig = go.Figure(go.Bar(
        x=_T_XLABELS,
        y=[None] * (_NUM_MODULES * _SENSORS),
        marker=dict(color=_T_COLORS),
        hovertemplate="%{x}<br><b>%{y}</b><extra></extra>",
    ))
    t_fig.update_layout(
        **_BAR_LAYOUT,
        height=320,
        yaxis=dict(title=dict(text="raw", standoff=4)),
    )

    return html.Div(style={"paddingTop": "14px"}, children=[

        # ── Zellspannungen ───────────────────────────────────────────────────
        html.Div(style=_CARD, children=[
            html.P("Zellspannungen (10 Module × 12 Zellen)", style=_SEC),
            dcc.Graph(
                id="cell_voltage_heatmap",
                figure=v_fig,
                config={"displayModeBar": True, "scrollZoom": True,
                        "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
            ),
            html.Div(style={"marginTop": "8px"}, children=[
                html.Span(["Min: ", html.B("–", id="v_stat_min", style=_STAT_VAL), " mV"],
                          style=_STAT_STYLE),
                html.Span(["Max: ", html.B("–", id="v_stat_max", style=_STAT_VAL), " mV"],
                          style=_STAT_STYLE),
                html.Span(["Δ: ",   html.B("–", id="v_stat_delta", style=_STAT_VAL), " mV"],
                          style=_STAT_STYLE),
                html.Span(["Avg: ", html.B("–", id="v_stat_avg", style=_STAT_VAL), " mV"],
                          style=_STAT_STYLE),
            ]),
        ]),

        # ── Zelltemperaturen ─────────────────────────────────────────────────
        html.Div(style=_CARD, children=[
            html.P("Zelltemperaturen (10 Module × 16 Sensoren)", style=_SEC),
            dcc.Graph(
                id="cell_temp_heatmap",
                figure=t_fig,
                config={"displayModeBar": True, "scrollZoom": True,
                        "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
            ),
            html.Div(style={"marginTop": "8px"}, children=[
                html.Span(["Min: ", html.B("–", id="t_stat_min", style=_STAT_VAL)],
                          style=_STAT_STYLE),
                html.Span(["Max: ", html.B("–", id="t_stat_max", style=_STAT_VAL)],
                          style=_STAT_STYLE),
                html.Span(["Avg: ", html.B("–", id="t_stat_avg", style=_STAT_VAL)],
                          style=_STAT_STYLE),
            ]),
        ]),
    ])
