from dash import html

from ui.cards import build_cell_voltage_card, build_cell_temperature_card


def build_cell_data_tab():
    """Build the complete 'Zellen' tab content."""
    return html.Div(style={"paddingTop": "14px"}, children=[
        build_cell_voltage_card(),
        build_cell_temperature_card(),
    ])
