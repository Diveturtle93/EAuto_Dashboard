from dash import Output, Input, State


def register_theme_callback(app):
    @app.callback(
        Output("theme-store", "data"),
        Output("theme-btn", "children"),
        Input("theme-btn", "n_clicks"),
        State("theme-store", "data"),
        prevent_initial_call=True,
    )
    def _toggle_theme(_, current):
        if current == "dark":
            return "light", "Dunkel"
        return "dark", "Hell"

    app.clientside_callback(
        """
        function(theme) {
            if (theme === 'light') {
                document.documentElement.classList.add('theme-light');
            } else {
                document.documentElement.classList.remove('theme-light');
            }
            return '';
        }
        """,
        Output("theme-dummy", "children"),
        Input("theme-store", "data"),
    )
