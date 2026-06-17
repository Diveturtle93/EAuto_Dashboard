import plotly.graph_objects as go
from dash import Input, Output, html, dcc

_ADC_MAX = 4095  # 12-bit ADC


def register_temperature_chart_callback(app):
    @app.callback(
        Output("temperature_chart", "children"),
        Input("snap", "data"),
    )
    def update_temperature_chart(snap):
        if not snap:
            return _empty_chart()

        L = snap.get("L", {})
        values = [
            L.get("temp_adc_1"),
            L.get("temp_adc_2"),
            L.get("temp_adc_3"),
            L.get("temp_adc_4"),
        ]

        labels = ["T1", "T2", "T3", "T4"]

        fig = go.Figure(go.Bar(
            x=labels,
            y=[v if v is not None else 0 for v in values],
            marker_color=["#3498db", "#2ecc71", "#e67e22", "#e74c3c"],
            text=[str(v) if v is not None else "–" for v in values],
            textposition="outside",
        ))

        fig.update_layout(
            yaxis=dict(range=[0, _ADC_MAX], title="ADC-Wert (12-bit)"),
            xaxis=dict(title="Temperatursensor"),
            margin=dict(t=30, b=40, l=50, r=20),
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            height=280,
            showlegend=False,
        )

        return dcc.Graph(figure=fig, config={"displayModeBar": False})


def _empty_chart():
    fig = go.Figure(go.Bar(x=["T1", "T2", "T3", "T4"], y=[0, 0, 0, 0],
                           marker_color="#cccccc"))
    fig.update_layout(
        yaxis=dict(range=[0, _ADC_MAX], title="ADC-Wert (12-bit)"),
        xaxis=dict(title="Temperatursensor"),
        margin=dict(t=30, b=40, l=50, r=20),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        height=280,
        showlegend=False,
    )
    return dcc.Graph(figure=fig, config={"displayModeBar": False})
