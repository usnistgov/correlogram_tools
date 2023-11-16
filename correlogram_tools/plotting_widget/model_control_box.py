import ipywidgets as widgets
import numpy as np

from .model_header_box import ModelHeaderBox
from .model_plotting_controls import ModelPlottingControls
from .model_definition_box import ModelDefinitionBox


class ModelControlBox:
    data_models = {}
    data_model_list = {}
    data_plot = {}
    saved_data = {}

    def __init__(self):

        # self.add_model(first=True)

        self.control_box = widgets.VBox(
            children=[
                ModelHeaderBox().model_header_box,
                ModelPlottingControls().model_plotting_controls,
            ],
            layout=dict(width="425px")
        )

        self.add_model(first=True)

        self.control_box.children[0].children[0].children[0].observe(self.go_click, names='value')
        self.control_box.children[-1].children[-1].children[-1].on_click(self.duplicate_model)

    def add_model(self, first=False):

        if first:
            index = 1

        else:

            index = int(np.max(list(self.data_models.keys()))) + 1
            new_options = list(self.control_box.children[0].children[0].children[0].options)
            new_options = list(new_options[:-1]) + list(['Model ' + str(index)]) + [new_options[-1]]
            self.control_box.children[0].children[0].children[0].options = new_options

        self.data_model_list['Model ' + str(index)] = index
        new_model_define_box = ModelDefinitionBox(index).model_definition_box
        self.data_models[index] = new_model_define_box
        self.data_plot[index] = False

        self.control_box.children[0].children[0].children[0].value = 'Model ' + str(index)

        self.control_box.children = [self.control_box.children[0]] + [self.data_models[index]] + [
            self.control_box.children[-1]]

    def go_click(self, dropdown):

        if self.control_box.children[0].children[0].children[0].value == 'Click to add new model...':
            self.add_model()
        else:
            index = self.data_model_list[self.control_box.children[0].children[0].children[0].value]
            self.control_box.children = [self.control_box.children[0]] + [self.data_models[index]] + [
                self.control_box.children[-1]]

    def duplicate_model(self, button: widgets.Widget) -> None:

        old_index = self.data_model_list[self.control_box.children[0].children[0].children[0].value]
        self.add_model()
        current_index = int(np.max(list(self.data_models.keys())))
        new_model = self.data_models[current_index]

        old_model_info = self.data_models[old_index]
        old_form = old_model_info.children[1].value
        old_structure = old_model_info.children[2].value
        old_combined = old_model_info.children[3].value

        new_model.children[1].value = old_form
        new_model.children[2].value = old_structure
        new_model.children[3].value = old_combined

        for i in range(0, len(old_model_info.children[-3].children[:])):
            old_value = old_model_info.children[-3].children[i].value
            old_desc = old_model_info.children[-3].children[i].description
            new_desc = new_model.children[-3].children[i].description
            if old_desc == new_desc:
                new_model.children[-3].children[i].value = old_value

        for i in range(0, len(old_model_info.children[-2].children[:])):
            old_value = old_model_info.children[-2].children[i].value
            old_desc = old_model_info.children[-2].children[i].description
            new_desc = new_model.children[-2].children[i].description
            if old_desc == new_desc:
                new_model.children[-2].children[i].value = old_value

        for i in range(0, len(old_model_info.children[-1].children[:])):
            old_value = old_model_info.children[-1].children[i].value
            old_desc = old_model_info.children[-1].children[i].description
            new_desc = new_model.children[-1].children[i].description
            if old_desc == new_desc:
                new_model.children[-1].children[i].value = old_value
