import ipywidgets as widgets
import numpy as np

from .model_control_box import ModelControlBox
from .plot_trio import PlotTrio


def make_sas_buttons():

    spacing_buttons = widgets.RadioButtons(
        options=["log scale", "linear scale"],
        disabled=False,
        value="log scale"
    )

    plot_buttons = widgets.RadioButtons(
        options=[
            "I(q) vs. q",
            "Guinier, ln(I(q)) vs. q^2",
            "Zimm, 1/I(q) vs. q^2",
            "Kratky, I(q)*q^2 vs. q"
        ],
        disabled=False,
        value="I(q) vs. q"
    )

    sas_buttons = widgets.HBox(children=[spacing_buttons, plot_buttons])

    return sas_buttons


def make_vis_buttons():

    spacing_buttons = widgets.RadioButtons(
        options=["log scale", "linear scale"],
        disabled=False,
        value="linear scale"
    )

    plot_buttons = widgets.RadioButtons(
        options=[
            "loss in visibility",
            "dark field"
        ],
        disabled=False,
        value="loss in visibility"
    )

    vis_buttons = widgets.HBox(children=[spacing_buttons, plot_buttons])

    return vis_buttons


class PlottingWidgetGrid:

    def __init__(self):

        grid = widgets.GridspecLayout(2, 2)
        self.model_control_box = ModelControlBox()
        grid[:, 0] = self.model_control_box.control_box

        title = widgets.Label("Correlogram-Tools Plotting Widget", style=dict(font_size="30px"))
        title.layout.padding = "30px 5px 50px 5px"

        self.plotting_widget = widgets.VBox(
            children=[
                title,
                widgets.HTML(value="<p>The dark_field-tools plotting widget enables the simultaneous plotting of "
                                   "small-angle scattering and dark field interferometry data. For more information "
                                   "about the available microstructure models, please reference the SasView "
                                   "documentation <a href=https://www.sasview.org/docs/user/qtgui/Perspectives"
                                   "/Fitting/models/index.html>here</a>.</p>", style=dict(font_size="15px")),
                widgets.HTML(value="<hr>"),
                grid
            ]
        )

        self.sas_buttons = make_sas_buttons()
        self.vis_buttons = make_vis_buttons()
        self.plots = PlotTrio(self.model_control_box, self.sas_buttons, self.vis_buttons)

        self.reset_plot_grid()

        self.model_control_box.control_box.children[-1].children[0].children[0].on_click(self.add_update_click)
        self.model_control_box.control_box.children[-1].children[0].children[1].on_click(self.add_update_click)
        self.model_control_box.control_box.children[-1].children[0].children[2].on_click(self.delete_click)
        self.model_control_box.control_box.children[0].children[1].children[0].on_click(self.clear_plots)
        self.model_control_box.control_box.children[0].children[1].children[1].on_click(self.export_plot_data)

        self.sas_buttons.children[1].observe(self.sas_buttons_change, names="value")
        self.sas_buttons.children[0].observe(self.sas_scaling_change, names="value")

        self.vis_buttons.children[1].observe(self.vis_buttons_change, names="value")
        self.vis_buttons.children[0].observe(self.vis_scaling_change, names="value")

    def reset_plot_grid(self):
        header = widgets.Label(value="Small Angle Scattering")
        header.style.font_size = "20px"
        self.plotting_widget.children[-1][0, 1] = widgets.VBox(children=[
            header, self.sas_buttons, self.plots.sas_figure
        ])

        header = widgets.Label(value="Dark Field Interferometry")
        header.style.font_size = "20px"
        self.plotting_widget.children[-1][1, 1] = widgets.VBox(children=[
            header, self.vis_buttons, self.plots.vis_figure
        ])

    def add_update_click(self, button):

        self.plots.add_update_click(button)
        self.reset_plot_grid()

    def delete_click(self, button):

        self.plots.delete_click(button)
        self.reset_plot_grid()

    def clear_plots(self, button):

        self.plots.clear_plots(button)
        self.reset_plot_grid()

    def export_plot_data(self, button):

        saved_data = self.model_control_box.saved_data
        data_plot = self.model_control_box.data_plot

        for i, check in data_plot.items():
            if check:
                q, Iq, aclength, vis, DF, label = saved_data[i]

                filename = f"model_{i}_qIq.csv"
                data = np.vstack((q, Iq)).T
                np.savetxt(filename, data, header="q (1/Ang), I(q) (1/cm)", delimiter=',')

                filename = f"model_{i}_df.csv"
                data = np.vstack((aclength, vis, DF)).T
                np.savetxt(
                    filename, data, header="autocorrelation length (Ang), loss in visibility, dark field", delimiter=','
                )

    def sas_buttons_change(self, value):
        if value["old"] == "I(q) vs. q":
            self.sas_buttons.children[0].value = "linear scale"
        elif value["new"] == "I(q) vs. q":
            self.sas_buttons.children[0].value = "log scale"

        self.add_update_click(value)

    def sas_scaling_change(self, value):
        scaling_type = value["new"].split()[0]
        self.plots.update_scaling_sas(scaling_type)

    def vis_buttons_change(self, value):
        self.add_update_click(value)

    def vis_scaling_change(self, value):
        scaling_type = value["new"].split()[0]
        self.plots.update_scaling_vis(scaling_type)
