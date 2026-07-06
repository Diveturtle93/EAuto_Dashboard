# Karte mit Balkendiagramm der Zelltemperaturen aller Module (10 Module x 16
# Sensoren). Wird per Callback (ui/callbacks/cell_data.py) via Patch() bei
# jedem neuen Snapshot aktualisiert.

import plotly.graph_objects as go
from dash import dcc, html

_NUM_MODULES = 10
_SENSORS     = 16

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

# One distinct color per module, repeated for each sensor in that module
_MOD_COLORS = [
    "#4C9BE8", "#E86B4C", "#4CE87A", "#E8C84C", "#9B4CE8",
    "#4CE8D8", "#E84C9B", "#8CE84C", "#E8A04C", "#4C4CE8",
]

_XLABELS = [f"M{m+1}-S{s+1}" for m in range(_NUM_MODULES) for s in range(_SENSORS)]
_COLORS  = [_MOD_COLORS[m] for m in range(_NUM_MODULES) for _ in range(_SENSORS)]


def build_cell_temperature_card():
    """Karte mit Balkendiagramm der Zelltemperaturen aller Module."""
    fig = go.Figure(go.Bar(
        x=_XLABELS,
        y=[None] * (_NUM_MODULES * _SENSORS),
        marker=dict(color=_COLORS),
        hovertemplate="%{x}<br><b>%{y}</b><extra></extra>",
    ))
    fig.update_layout(
        **_BAR_LAYOUT,
        height=320,
        yaxis=dict(title=dict(text="raw", standoff=4)),
    )

    return html.Div(
        className="card",
        children=[
            html.P("Zelltemperaturen (10 Module × 16 Sensoren)", className="card-sec"),
            dcc.Graph(
                id="cell_temp_heatmap",
                figure=fig,
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
        ],
    )
