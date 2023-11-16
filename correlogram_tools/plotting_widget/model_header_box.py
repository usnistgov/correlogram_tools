import ipywidgets as widgets


def make_model_list_dropdown() -> widgets.Widget:
    model_list_dropdown = widgets.Dropdown(
        options=['Model 1', "Click to add new model..."],
        value='Model 1',
        description='Select Model',
        style={
            'description_width': '100px'
        },
        layout={
            'width': '400px'
        }
    )

    return model_list_dropdown


def make_model_list_box() -> widgets.Widget:
    model_list_box = widgets.HBox(
        children=[make_model_list_dropdown()],
        layout={}
    )

    return model_list_box


def make_clear_button() -> widgets.Widget:
    clear_button = widgets.Button(
        description='Clear All Plots',
        icon='chart-line',
        style={
            'button_color': '#9ecae1'
        },
        layout={'width': '400px'},
        tooltip="Removes all traces from the small-angle scattering and dark field plots on the right."
    )

    return clear_button


def make_export_button() -> widgets.Widget:
    export_button = widgets.Button(
        description='Export Plot Data',
        icon='save',
        style={
            'button_color': '#4292c6'
        },
        layout={'width': '400px'},
        tooltip="Exports SAS and dark field data from the plots to csv files in the working directory."
    )

    return export_button


class ModelHeaderBox:

    def __init__(self):
        model_list = make_model_list_box()

        clear_button = make_clear_button()
        # clear_button.on_click(clear_plots_func)

        export_button = make_export_button()
        # export_button.on_click(export_data_func)

        self.model_header_box = widgets.VBox(
            children=[
                model_list,
                widgets.HBox(children=[clear_button, export_button])
            ]
        )
