import ipywidgets as widgets


def make_add_button():
    add_button = widgets.Button(
        description='Add to Plot',
        icon='plus',
        style={'button_color': '#c6dbef'},
        layout={'width': '100px'},
        tooltip="Adds currently selected model to the plots on the right."
    )

    return add_button


def make_update_button():
    update_button = widgets.Button(
        description='Update Plot',
        icon='refresh',
        style={'button_color': '#9ecae1'},
        layout={'width': '100px'},
        tooltip="Updates currently selected model on the plots after parameter changes."
    )

    return update_button


def make_delete_button():
    delete_button = widgets.Button(
        description='Delete',
        icon='times',
        style={'button_color': '#6baed6'},
        layout={'width': '100px'},
        tooltip="Removes currently selected model from the plots on the right."
    )

    return delete_button


def make_duplicate_button():
    duplicate_button = widgets.Button(
        description='Duplicate',
        icon='copy',
        style={'button_color': '#4292c6'},
        layout={'width': '100px'},
        tooltip="Duplicates the currently selected model and parameters to a new model."
    )

    return duplicate_button


class ModelPlottingControls:

    def __init__(self):
        # setting up control buttons for the plotting

        add_button = make_add_button()
        # add_button.on_click(add_update_click)

        update_button = make_update_button()
        # update_button.on_click(add_update_click)

        delete_button = make_delete_button()
        # delete_button.on_click(delete_click)

        duplicate_button = make_duplicate_button()

        self.control_buttons = widgets.HBox(
            children=[
                add_button,
                update_button,
                delete_button,
                duplicate_button
            ]
        )

        # creating full plotting control box
        self.model_plotting_controls = widgets.VBox(
            children=[
                self.control_buttons,
            ]
        )
