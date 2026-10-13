#-----------------------------------------------------------------------
# Titel		:	theme.py
#-----------------------------------------------------------------------
# Sprache	:	Python
# Datum		:	28.06.2026
# Version	:	1.0
# Autor		:	Diveturtle93
# Projekt	:	EAuto_Dashboard
# Quelle	:
#-----------------------------------------------------------------------

# Einfuegen der standard Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Einfuegen der externen Module
#-----------------------------------------------------------------------
from dash import Input, Output, State
#-----------------------------------------------------------------------

# Einfuegen der eigenen Module
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Definiere Debug-Symbole
#-----------------------------------------------------------------------
DEBUG_THEME										= False
#-----------------------------------------------------------------------

# Version definieren
#-----------------------------------------------------------------------
THEME_MAJOR										= 1
THEME_MINOR										= 0
THEME_PATCH										= 0
THEME_DEV										= 0
#-----------------------------------------------------------------------

# Konstanten definieren
#-----------------------------------------------------------------------
# Clientside-JS: setzt bzw. entfernt die CSS-Klasse theme-light am <html>-Element
_THEME_JS										= """
        function(theme) {
            if (theme === 'light') {
                document.documentElement.classList.add('theme-light');
            } else {
                document.documentElement.classList.remove('theme-light');
            }
            return '';
        }
        """
#-----------------------------------------------------------------------

# Variablen definieren
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

# Callbacks fuer den Hell/Dunkel-Umschalter registrieren
#-----------------------------------------------------------------------
def registerThemeCallback (app):
	# Theme wechseln, die Aufschrift zeigt das jeweils andere Theme
	@app.callback(
		Output("theme-store", "data"),
		Output("theme-btn", "children"),
		Input("theme-btn", "n_clicks"),
		State("theme-store", "data"),
		prevent_initial_call=True,
	)
	def _toggleTheme (_, current):
		if current == "dark":
			return "light", "Dunkel"

		return "dark", "Hell"

	# Theme im Browser anwenden
	app.clientside_callback(
		_THEME_JS,
		Output("theme-dummy", "children"),
		Input("theme-store", "data"),
	)
#-----------------------------------------------------------------------
