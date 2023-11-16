import ipywidgets as widgets

import sasmodels
import sasmodels.core
import sasmodels.bumps_model


def interpret_model_dropdowns(form_factor_value, structure_factor_value):
    kernel_name = ''
    if form_factor_value != 'None':
        kernel_name += form_factor_value
        if structure_factor_value != 'None':
            kernel_name += '@'
            kernel_name += structure_factor_value
        elif structure_factor_value != 'None':
            kernel_name += structure_factor_value

    return kernel_name


def get_kernel_name(combined_model_box_value, form_factor_value, structure_factor_value):

    if len(combined_model_box_value) > 0:
        kernel_name = combined_model_box_value
        try:
            kernel_test = sasmodels.core.load_model(kernel_name)
        except ModuleNotFoundError:
            print("ERROR: not a valid combined model string; ignoring text and using form factor and structure "
                  "factor dropdown models.")
            return interpret_model_dropdowns(
                form_factor_value,
                structure_factor_value
            )
        else:
            return kernel_name
    else:
        return interpret_model_dropdowns(
            form_factor_value,
            structure_factor_value
        )


def make_form_factor_dropdown() -> widgets.Dropdown:
    form_factor_list = ['None']
    form_factor_list += [x for x in sasmodels.core.list_models(kind='all') if
                         not sasmodels.core.load_model(x).info.structure_factor]

    form_factor_dropdown = widgets.Dropdown(
        options=form_factor_list,
        value='sphere',
        description='Form Factor',
        style={'description_width': '125px'},
        layout={'width': '400px'},
    )

    return form_factor_dropdown


def make_structure_factor_dropdown() -> widgets.Dropdown:
    structure_factor_list = ['None']
    structure_factor_list += [x for x in sasmodels.core.list_models(kind='all') if
                              sasmodels.core.load_model(x).info.structure_factor]

    structure_factor_dropdown = widgets.Dropdown(
        options=structure_factor_list,
        value='None',
        description='Structure Factor',
        style={'description_width': '125px'},
        layout={'width': '400px'},
    )

    return structure_factor_dropdown


def make_combined_model_box() -> widgets.Widget:

    combined_model_box = widgets.Text(
        placeholder='Enter combined model and hit Enter.',
        description='Combined Model:',
        style={'description_width': '125px'},
        layout={'width': '400px'},
        continuous_update=False,
    )

    return combined_model_box

# def get_combined_model_button():
#
#     combined_model_button = widgets.Button(
#         description='GO',
#         style={
#             'button_color': '#9ecae1'
#         },
#         layout={'width': '50px'},
#         tooltip="Submit combined model string for modeling."
#     )
#
#     return combined_model_button


def make_parameter_box(param, units=None) -> widgets.Widget:
    if units:
        param_name = f"{param.name} ({units})"
    else:
        param_name = param.name
    parameter_box = widgets.FloatText(
        value=param.value,
        description=param_name,
        style={'description_width': '200px'},
        layout={'width': '400px'},
    )

    if param.name == 'background':
        parameter_box.disabled = True
        parameter_box.value = 0
    return parameter_box


def make_autocorrelation_label() -> widgets.Widget:
    autoc_label = widgets.Label(
        value='Autocorrelation Length:'
    )

    return autoc_label


def make_autocorrelation_min():
    autoc_min = widgets.FloatText(
        value=0,
        description='Min (Ang)',
        style={'description_width': '200px'},
        layout={'width': '400px'},
    )

    return autoc_min


def make_autocorrelation_max() -> widgets.Widget:
    autoc_max = widgets.FloatText(
        value=1000,
        description="Max (Ang)",
        style={'description_width': '200px'},
        layout={'width': '400px'},
    )

    return autoc_max


def make_autocorrelation_count() -> widgets.Widget:
    autoc_count = widgets.IntText(
        value=1000,
        description='Number of Points',
        style={'description_width': '200px'},
        layout={'width': '400px'},
    )

    return autoc_count


def make_measurement_label() -> widgets.Widget:
    meas_label = widgets.Label(
        value="Measurement & Sample Details:"
    )

    return meas_label


def make_measurement_wavelength() -> widgets.Widget:
    meas_wavelength = widgets.FloatText(
        value=4.2,
        description='Wavelength (Ang)',
        style={'description_width': '200px'},
        layout={'width': '400px'},
    )

    return meas_wavelength


def make_measurement_thickness() -> widgets.Widget:
    meas_thickness = widgets.FloatText(
        value=0.1,
        description="Thickness (cm)",
        style={'description_width': '200px'},
        layout={'width': '400px'},
    )

    return meas_thickness


class ModelDefinitionBox:

    def __init__(self, index):

        self.index = int(index)

        # setting up model name and selection

        self.model_name_box = self.make_model_name_box()

        self.form_factor_dropdown = make_form_factor_dropdown()

        self.structure_factor_dropdown = make_structure_factor_dropdown()

        self.combined_model_box = make_combined_model_box()

        self.kernel_name = get_kernel_name(
            self.combined_model_box.value,
            self.form_factor_dropdown.value,
            self.structure_factor_dropdown.value
        )

        # setting up model parameters

        self.parameters = widgets.VBox(
            children=self.make_parameter_children(),
            layout=dict(height="400px")
        )

        self.form_factor_dropdown.observe(self.update_params, names='value')
        self.structure_factor_dropdown.observe(self.update_params, names='value')
        self.combined_model_box.observe(self.update_params, names='value')

        # setting up autocorrelation box

        autoc_label = make_autocorrelation_label()
        autoc_min = make_autocorrelation_min()
        autoc_max = make_autocorrelation_max()
        autoc_count = make_autocorrelation_count()

        self.autocorrelation_box = widgets.VBox(
            children=[autoc_label, autoc_min, autoc_max, autoc_count]
        )

        # setting up measurement box

        meas_label = make_measurement_label()
        meas_wavelength = make_measurement_wavelength()
        meas_thickness = make_measurement_thickness()

        self.measurement_box = widgets.VBox(
            children=[meas_label, meas_wavelength, meas_thickness],
        )

        # creating full model definition box
        self.model_definition_box = widgets.VBox(
            children=[
                self.model_name_box,
                self.form_factor_dropdown,
                self.structure_factor_dropdown,
                self.combined_model_box,
                widgets.Label(value='Model Parameters:', style={}),
                self.parameters,
                self.autocorrelation_box,
                self.measurement_box
            ]
        )

    def make_model_name_box(self):

        model_name_box = widgets.Text(
            value=f'Model{str(self.index)}',
            description='Custom Name',
            style={'description_width': '125px'},
            layout={'width': '400px'},
        )

        return model_name_box

    def make_parameter_children(self):

        kernel = get_kernel_name(
            self.combined_model_box.value,
            self.form_factor_dropdown.value,
            self.structure_factor_dropdown.value
        )
        self.kernel_name = kernel
        param_list = []
        if kernel != '':
            kernel = sasmodels.core.load_model(kernel)
            unit_dict = {param.name: param.units for param in kernel.info.parameters.call_parameters
                         if param.units != ''}
            model = sasmodels.bumps_model.Model(kernel)
            for key, param in model.parameters().items():
                if "M0" in param.name or "mtheta" in param.name or "mphi" in param.name or "up_" in param.name:
                    pass
                else:
                    if param.name in unit_dict.keys():
                        units = unit_dict[param.name]
                    else:
                        units = None
                    param_list.append(make_parameter_box(param, units=units))
        return param_list

    def update_params(self, button):

        self.parameters.children = self.make_parameter_children()
