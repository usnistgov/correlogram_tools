import plotly.graph_objs as go
import numpy as np
import sasmodels
import sasmodels.core
import sasmodels.bumps_model

from correlogram_tools.hankel import get_qIq, visibility, dark_field
from .model_definition_box import get_kernel_name


class PlotTrio:

    sas_figure = None
    vis_figure = None

    def __init__(self, model_control_box, sas_buttons, vis_buttons):

        self.model_control_box = model_control_box
        self.sas_buttons = sas_buttons
        self.vis_buttons = vis_buttons

        # initiate the sas figure

        self.initiate_plots()

    def generate_plots(self):

        #         fig = go.FigureWidget()

        indices = []
        # colors = px.colors.qualitative.Safe
        colors = [
            'rgb(204, 102, 119)',
            'rgb(51, 34, 136)',
            'rgb(17, 119, 51)',
            'rgb(136, 204, 238)',
            'rgb(136, 34, 85)',
            'rgb(153, 153, 51)',
            'rgb(170, 68, 153)',
            'rgb(221, 204, 119)',
            'rgb(68, 170, 153)',
        ]

        # determine which models should be plotted
        for key, value in self.model_control_box.data_plot.items():
            if value:
                indices.append(key)

        for index in indices:
            if index not in self.model_control_box.saved_data.keys():
                model_details = self.model_control_box.data_models[index]
                label = model_details.children[0].value

                form_factor_value = model_details.children[1].value
                structure_factor_value = model_details.children[2].value
                combined_model_box_value = model_details.children[3].value
                kernel_name = get_kernel_name(combined_model_box_value, form_factor_value, structure_factor_value)

                param_dict = {}
                params = model_details.children[-3].children[:]
                for param in params:
                    param_name = param.description.split()[0]
                    param_dict[param_name] = param.value

                amin, amax, anum = [x.value for x in list(model_details.children[-2].children[1:])]
                aclength = np.linspace(amin, amax, anum)
                wavelength, thickness = [x.value for x in list(model_details.children[-1].children[1:])]

                kernel = sasmodels.core.load_model(kernel_name)
                model = sasmodels.bumps_model.Model(kernel, **param_dict)

                q, Iq = get_qIq(aclength, model, q_logstep=0.001)
                vis = visibility(aclength, q, Iq, wavelength, thickness).reshape(-1)
                DF = dark_field(aclength, q, Iq, wavelength, thickness).reshape(-1)
                self.model_control_box.saved_data[index] = (q, Iq, aclength, vis, DF, label)

            else:
                q, Iq, aclength, vis, DF, label = self.model_control_box.saved_data[index]

            sas_choice = self.sas_buttons.children[1].value
            if "Guinier" in sas_choice:
                self.sas_figure.add_trace(go.Scatter(x=q ** 2, y=np.log(Iq), name=label, line_color=colors[index-1]))
            elif "Zimm" in sas_choice:
                self.sas_figure.add_trace(go.Scatter(x=q ** 2, y=np.reciprocal(Iq), name=label,
                                                     line_color=colors[index-1]))
            elif "Kratky" in sas_choice:
                self.sas_figure.add_trace(go.Scatter(x=q, y=Iq * q ** 2, name=label, line_color=colors[index-1]))
            else:
                self.sas_figure.add_trace(go.Scatter(x=q, y=Iq, name=label, line_color=colors[index-1]))

            df_choice = self.vis_buttons.children[1].value
            if df_choice == "loss in visibility":
                self.vis_figure.add_trace(go.Scatter(x=aclength, y=vis, name=label, line_color=colors[index - 1]))
            else:
                self.vis_figure.add_trace(go.Scatter(x=aclength, y=DF, name=label, line_color=colors[index - 1]))

    def initiate_plots(self):

        # initiate the sas figure

        pad = 20

        fig = go.FigureWidget()

        fig.update_layout(
            margin=dict(l=pad, r=pad, t=pad * 2, b=pad),
        )
        fig.update_layout(plot_bgcolor='white')
        fig.update_xaxes(gridcolor='lightgrey', zeroline=True, zerolinecolor='black', color='black', linecolor='black',
                         mirror=True, tickformat='.1e')
        fig.update_yaxes(gridcolor='lightgrey', zeroline=True, zerolinecolor='black', color='black', linecolor='black',
                         mirror=True, tickformat='.1e')

        if self.sas_buttons.children[0].value == "log scale":
            fig.update_xaxes(type='log')
            fig.update_yaxes(type='log')
        else:
            fig.update_xaxes(type="linear")
            fig.update_yaxes(type="linear")

        sas_choice = self.sas_buttons.children[1].value
        if "Guinier" in sas_choice:
            fig.update_xaxes(title_text="q^2 (Ang^-2)")
            fig.update_yaxes(title_text="ln(I(q))")
        elif "Zimm" in sas_choice:
            fig.update_xaxes(title_text="q^2 (Ang^-2)")
            fig.update_yaxes(title_text="1/I(q)")
        elif "Kratky" in sas_choice:
            fig.update_xaxes(title_text="q (Ang^-1)")
            fig.update_yaxes(title_text="I(q)q^2 (Ang^-2 cm^-1)")
        else:
            fig.update_xaxes(title_text="q (Ang^-1)")
            fig.update_yaxes(title_text="I(q) (1/cm)")

        self.sas_figure = fig

        # initiate the interferometry figure

        fig = go.FigureWidget()

        fig.update_layout(
            margin=dict(l=pad, r=pad, t=pad * 2, b=pad),
            yaxis_range=[0, 1]
        )

        fig.update_layout(plot_bgcolor='white')
        fig.update_xaxes(gridcolor='lightgrey', zeroline=False, zerolinecolor='black', color='black', linecolor='black',
                         mirror=True)
        fig.update_yaxes(gridcolor='lightgrey', zeroline=False, zerolinecolor='black', color='black', linecolor='black',
                         mirror=True)

        if self.vis_buttons.children[0].value == "log scale":
            fig.update_xaxes(type='log')
            fig.update_yaxes(type='log')
        else:
            fig.update_xaxes(type="linear")
            fig.update_yaxes(type="linear")

        vis_choice = self.vis_buttons.children[1].value
        if vis_choice == "loss in visibility":
            fig.update_xaxes(title_text="autocorrelation length (Ang)")
            fig.update_yaxes(title_text="loss in visibility")
        else:
            fig.update_xaxes(title_text="autocorrelation length (Ang)")
            fig.update_yaxes(title_text="dark field")

        self.vis_figure = fig

    def update_scaling_sas(self, scaling_type):
        self.sas_figure.update_xaxes(type=scaling_type)
        self.sas_figure.update_yaxes(type=scaling_type)

    def update_scaling_vis(self, scaling_type):
        self.vis_figure.update_xaxes(type=scaling_type)
        self.vis_figure.update_yaxes(type=scaling_type)

    def add_update_click(self, button):
        index = self.model_control_box.data_model_list[
            self.model_control_box.control_box.children[0].children[0].children[0].value]
        self.model_control_box.saved_data.pop(index, None)
        self.model_control_box.data_plot[index] = True

        self.initiate_plots()
        self.generate_plots()

    def delete_click(self, button):
        index = self.model_control_box.data_model_list[
            self.model_control_box.control_box.children[0].children[0].children[0].value]
        self.model_control_box.saved_data.pop(index, None)
        self.model_control_box.data_plot[index] = False

        self.initiate_plots()
        self.generate_plots()

    def clear_plots(self, button):
        for i in self.model_control_box.data_plot.keys():
            self.model_control_box.data_plot[i] = False

        self.initiate_plots()
        self.generate_plots()
