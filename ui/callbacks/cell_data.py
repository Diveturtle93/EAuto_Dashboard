from dash import Input, Output, Patch

_NUM_MODULES = 10
_CELLS       = 12
_SENSORS     = 16

_CHART_IDS = ["cell_voltage_heatmap", "cell_temp_heatmap"]

# Clientside JS: runs AFTER the theme-class callback (chained via theme-dummy),
# reads --chart-text and --chart-grid from CSS and applies them to all charts.
# Backgrounds are transparent in Python so the CSS-styled card shows through.
_RELAYOUT_JS = """
function(_) {
    var style = getComputedStyle(document.documentElement);
    var text = style.getPropertyValue('--chart-text').trim();
    var grid = style.getPropertyValue('--chart-grid').trim();
    if (!text) return '';
    var layout = {
        'font.color':      text,
        'xaxis.color':     text,
        'xaxis.gridcolor': grid,
        'xaxis.linecolor': grid,
        'yaxis.color':     text,
        'yaxis.gridcolor': grid,
        'yaxis.linecolor': grid,
        'yaxis.title.font.color': text
    };
    %s.forEach(function(gid) {
        try {
            var el = document.getElementById(gid);
            if (el) Plotly.relayout(el, layout);
        } catch(e) {}
    });
    return '';
}
""" % str(_CHART_IDS)


def register_cell_data_callbacks(app):

    # ── Theme-aware chart background (clientside, CSS-driven) ────────────────
    app.clientside_callback(
        _RELAYOUT_JS,
        Output("chart-theme-dummy", "children"),
        Input("theme-dummy", "children"),
    )

    # ── Cell voltages ─────────────────────────────────────────────────────────
    @app.callback(
        Output("cell_voltage_heatmap", "figure"),
        Output("v_stat_min",   "children"),
        Output("v_stat_max",   "children"),
        Output("v_stat_delta", "children"),
        Output("v_stat_avg",   "children"),
        Input("snap", "data"),
        prevent_initial_call=True,
    )
    def _update_voltages(snap):
        patch = Patch()
        if not snap:
            patch["data"][0]["y"] = [None] * (_NUM_MODULES * _CELLS)
            return patch, "–", "–", "–", "–"

        L = snap.get("L", {})
        y = [L.get(f"cell_v_m{m}_c{c}") for m in range(_NUM_MODULES) for c in range(_CELLS)]
        patch["data"][0]["y"] = y

        vals = [v for v in y if v is not None]
        if not vals:
            return patch, "–", "–", "–", "–"

        mn, mx = min(vals), max(vals)
        avg = round(sum(vals) / len(vals))
        return patch, str(mn), str(mx), str(mx - mn), str(avg)

    # ── Cell temperatures ─────────────────────────────────────────────────────
    @app.callback(
        Output("cell_temp_heatmap", "figure"),
        Output("t_stat_min", "children"),
        Output("t_stat_max", "children"),
        Output("t_stat_avg", "children"),
        Input("snap", "data"),
        prevent_initial_call=True,
    )
    def _update_temperatures(snap):
        patch = Patch()
        if not snap:
            patch["data"][0]["y"] = [None] * (_NUM_MODULES * _SENSORS)
            return patch, "–", "–", "–"

        L = snap.get("L", {})
        y = [L.get(f"cell_t_m{m}_s{s}") for m in range(_NUM_MODULES) for s in range(_SENSORS)]
        patch["data"][0]["y"] = y

        vals = [v for v in y if v is not None]
        if not vals:
            return patch, "–", "–", "–"

        mn, mx = min(vals), max(vals)
        avg = round(sum(vals) / len(vals))
        return patch, str(mn), str(mx), str(avg)
