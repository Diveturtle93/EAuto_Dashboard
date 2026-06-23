import plotly.graph_objects as go
from dash import Input, Output, Patch, dcc

_ADC_MAX = 4095  # 12-bit ADC
_LABELS = ["T1", "T2", "T3", "T4"]
_COLORS = ["#f97316", "#60a5fa", "#34d399", "#f87171"]
_LAYOUT = dict(
    yaxis=dict(
        range=[0, _ADC_MAX], title="ADC-Wert (12-bit)",
        color="#9099a8", gridcolor="#252836", linecolor="#252836", zerolinecolor="#252836",
    ),
    xaxis=dict(
        title="Temperatursensor",
        color="#9099a8", gridcolor="#252836", linecolor="#252836",
    ),
    margin=dict(t=30, b=40, l=50, r=20),
    plot_bgcolor="#161922",
    paper_bgcolor="#161922",
    font=dict(color="#9099a8"),
    height=280,
    showlegend=False,
)


def build_temperature_graph():
    """Returns a static dcc.Graph for the layout — data updated via Patch()."""
    fig = go.Figure(
        go.Bar(x=_LABELS, y=[0, 0, 0, 0], marker_color=_COLORS,
               text=["–", "–", "–", "–"], textposition="outside"),
    )
    fig.update_layout(**_LAYOUT)
    return dcc.Graph(id="temperature_graph", figure=fig,
                     config={"displayModeBar": False})


def register_temperature_chart_callback(app):
    @app.callback(
        Output("temperature_graph", "figure"),
        Input("snap", "data"),
        prevent_initial_call=True,
    )
    def update_temperature_chart(snap):
        patch = Patch()
        if not snap:
            patch["data"][0]["y"] = [0, 0, 0, 0]
            patch["data"][0]["text"] = ["–", "–", "–", "–"]
            return patch

        L = snap.get("L", {})
        raw = [L.get(f"temp_adc_{i}") for i in range(1, 5)]
        patch["data"][0]["y"] = [v if v is not None else 0 for v in raw]
        patch["data"][0]["text"] = [str(v) if v is not None else "–" for v in raw]
        return patch
