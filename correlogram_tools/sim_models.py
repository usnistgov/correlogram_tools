import os
from string import ascii_uppercase
import json

import numpy as np

import sasmodels.core

from .sim_config import SimConfig
from .sim_measurements import range_interpreter
from . import sasmodels_volumes as smvolumes


def has_structure_factor(sasmodel_name):
    """Determines whether a structure factor model is present in the full combined model."""
    if "@" in sasmodel_name:
        is_structure_factor = True
    elif sasmodels.core.load_model(sasmodel_name).info.structure_factor:
        is_structure_factor = True
    else:
        is_structure_factor = False
    return is_structure_factor


def random_values(size, range_min, range_max):
    """Returns a list of length 'size' of random draws from the range [min, max)."""
    return list(np.random.random_sample(size) * np.absolute(range_max - range_min) + np.min([range_min, range_max]))


def param_interpreter(mode, value: list, n_roi):
    """
    Interprets the mode and value pair for the parameter.
    Returns a list of values with length n_roi (one value per ROI specified).

    Parameters
    ----------
    mode : str
        Parameter mode defined in the experiment config. Accepted keywords are:
         - "range"
         - "user-defined"
         - "random-single"
         - "random"
    value : list
        Paired value to the mode specified. For formatting of the value for each mode, see the sim_template.js file.
    n_roi : int
        Number of ROI's in the model group that the parameter is applied to. The function will return a list of
        values with length n_roi (one value per ROI specified in the group). These could be unique or the same value
        depending on the mode selected.
    """

    if mode == "range":
        values = range_interpreter(value)
        if len(values) != n_roi:
            raise Exception(f"Incorrect length of range values ({value}) provided for a {mode} parameter mode. This"
                            f"should be equal to the number of ROIs for this model.")
    elif mode == "user-defined":
        if len(value) == 1:
            values = value * n_roi
        elif len(value) == n_roi:
            values = value
        else:
            raise Exception(f"Incorrect length of parameter values ({value}) provided for a {mode} parameter"
                            f"mode. Length of the value list should be equal to 1 (all ROI's have equal value"
                            f"for this parameter), or equal to the number of ROI's in this model group.")
    elif mode == "random-single":
        values = random_values(1, value[0], value[1]) * n_roi
    elif mode == "random":
        values = random_values(n_roi, value[0], value[1])
    else:
        raise Exception(f"Invalid type of parameter mode used: {mode}. Accepted modes include 'range', 'random',"
                        f"'random-single', and 'user-defined'.")
    return values


def component_interpreter(component_dict):
    """Interprets the component mode and returns (formula, density) of the material."""

    try:
        component_mode = component_dict["component_mode"]
    except KeyError:
        raise KeyError(f"Missing component mode in {component_dict}.")

    try:
        component_value = component_dict["value"]
    except KeyError:
        raise KeyError(f"Missing component value in {component_dict}.")

    if component_mode == "molecular-formula":
        formula = component_value
        try:
            density = component_dict["density"]
        except KeyError:
            raise KeyError(f"Missing component density in {component_dict}.")

    elif component_mode == "component-library":
        filename = component_value.split('.')[0]
        component_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "component_library")
        component_path = os.path.join(component_path, filename + '.json')
        try:
            with open(component_path) as file:
                component = json.load(file)[filename]
                file.close()
        except Exception:
            raise Exception(f"{component_value} is not an available component in the component library.")
        formula = component["formula"]
        density = component["density"]

    else:
        raise KeyError(f"Invalid mode of {component_mode} for component {component_dict}.")

    return formula, density


def model_name_interpreter(model_name):
    """
    Interprets the model name defined by the user which could be a mixture model and include digit identifiers per
    part. This function will return the full user-defined model name, a list of user-defined model parts, full
    sasmodels accepted model name, a list of sasmodels accepted model parts, the sasmodels letter prefixes, and a list
    of the operators used.

    The sasmodel prefixes will follow order of operations for mixture models and then are assigned left to right (see
    Example 2 below). A combination of + or * can be used, but parentheses are not accepted, so simple equations only.
    For a structure factor interaction, the @ symbol (e.g., sphere@hardsphere) or the * symbol (e.g., sphere*hardsphere)
    can be used, they are equivalent, for two models only (only one @ symbol per model). However, the @ symbol cannot be
    used with other operators, i.e., "cylinder+sphere@hardsphere" would not be accepted but "cylinder+sphere*hardsphere"
    is accepted. If the @ symbol is used to indicate structure factor, the model parameters can be combined without
    prefixes.

    Example 1: model_name = "sphere1+sphere2+cylinder1" would return:
        ("sphere1+sphere2+cylinder1",
         ["sphere1", "sphere2", "cylinder1"],
         "sphere+sphere+cylinder",
         ["sphere", "sphere", "cylinder"],
         ["A_", "B_", "C_"],
         ["+", "+"])

    Example 2: model_name = "cylinder1+sphere*hardsphere" would return:
        ("cylinder1+sphere*hardsphere",
         ["cylinder1", "sphere", "hardsphere"],
         "cylinder+sphere*hardsphere",
         ["cylinder", "sphere", "hardsphere"],
         ["C_", "A_", "B_"],
         ["+", "*"])

    Example 3: model_name = "sphere1@hardsphere" would return:
        ("sphere1@hardsphere",
         ["sphere1", "hardsphere"],
         "sphere@hardsphere",
         ["sphere", "hardsphere"],
         ["", ""],
         ["@"],
    """

    if "@" in model_name:
        if "+" in model_name or "*" in model_name:
            raise Exception(f"Improper use of operators +, * combined with @ in {model_name}.")
        model_name_parts = model_name.split("@")
        if len(model_name_parts) > 2:
            raise Exception(f"Only one @ operator allowed for each combined model but more were found in {model_name}.")
        sasmodel_name_parts = [x[:-1] if x[-1].isdigit() else x for x in model_name_parts]
        if (sasmodels.core.load_model_info(sasmodel_name_parts[0]).structure_factor
                or not sasmodels.core.load_model_info(sasmodel_name_parts[1]).structure_factor):
            raise Exception(f"When using structure factors, the model format should be form_factor@structure_factor.")
        sasmodel_name = '@'.join(sasmodel_name_parts)
        return model_name, model_name_parts, sasmodel_name, sasmodel_name_parts, ["", ""], ["@"]
    elif "+" in model_name or "*" in model_name:
        split_sum = model_name.split("+")
        split_mult = [[x] if "*" not in x else x.split("*") for x in split_sum]
        model_name_parts = [x for sublist in split_mult for x in sublist]
        sasmodel_name_parts = [x[:-1] if x[-1].isdigit() else x for x in model_name_parts]
        operators = [item for sublist in
                     ["+" if len(x) == 1 else ["*"]*(len(x)-1)+["+"] for x in split_mult] for item in sublist][:-1]
        prefixes = [""]*len(model_name_parts)
        p_index = 0
        mult_index = list(set([item for sublist in [[i, i+1]
                                                    for i, o in enumerate(operators) if o == "*"] for item in sublist]))
        for i in mult_index:
            prefixes[i] = ascii_uppercase[p_index] + "_"
            p_index += 1
        for i, p in enumerate(prefixes):
            if p == "":
                prefixes[i] = ascii_uppercase[p_index] + "_"
                p_index += 1

        sasmodel_name = [item for sublist in [[sn, o] for sn, o
                                              in zip(sasmodel_name_parts, operators)]+[[sasmodel_name_parts[-1]]]
                         for item in sublist]
        sasmodel_name = "".join(sasmodel_name)

        return model_name, model_name_parts, sasmodel_name, sasmodel_name_parts, prefixes, operators
    else:
        model_name_parts = [model_name]
        sasmodel_name_parts = [x[:-1] if x[0-1].isdigit() else x for x in model_name_parts]
        sasmodel_name = sasmodel_name_parts[0]
        prefixes = [""]
        operators = []
        return model_name, model_name_parts, sasmodel_name, sasmodel_name_parts, prefixes, operators


def get_model_parts(model) -> dict:
    model_name = model["model"]["model_name"]
    roi = model["roi"]
    model_parts = {}
    for part in model["model"]["model_parts"]:
        part_name = part["part_name"]
        model_parts[part_name] = {}
        try:
            model_parts[part_name]["parameters"] = part["parameters"]
        except KeyError:
            model_parts[part_name]["parameters"] = {}
        except Exception:
            raise Exception(f"Error in reading part parameters for {model_name} model for ROIs {roi}.")
        try:
            model_parts[part_name]["sample_components"] = part["sample_components"]
        except KeyError:
            raise KeyError(f"Missing sample components for {part_name} in {model_name} model for ROIs {roi}.")
        except Exception:
            Exception(f"Error in reading sample components for {model_name} model for ROIs {roi}.")

    return model_parts

# CMW: old function, this is now handled with the combined model_name provided is separated into its components
# def get_prefix_list(model_name_parts) -> list:
#     """returns a list of the letter prefixes for combined SasView models"""
#
#     if len(model_name_parts) > 26:  # right now this is only based on the letter prefix
#         raise Exception(f"Too many models in this combined model: {model_name_parts}")
#     elif len(model_name_parts) == 1:
#         prefix = [""]
#     else:
#         prefix = []
#         for p in ascii_uppercase[:len(model_name_parts)]:
#             prefix.append(p + "_")
#
#     return prefix


class SimModels(SimConfig):
    """
    The SimModels class inherits the SimConfig class and generates the parameter sets for the SasView/sasmodels
    models of the ROIs defined in the simulation experiment configuration.

    Attributes
    ----------
    model_defaults : dict
        Reference dictionary of the default parameter values, ranges, and units for SasView models called in the
        simulation experiment configuration loaded from the sasmodels_defaults directory.
    open_roi : int
        The region(s) of interest (ROI) defined as the open beam or background region of the sample image.
        This will be a constant value across all simulated images (1) and will have a thickness of 0.
    models : dict
        Dictionary of the SasView/sasmodels model and the parameters for each ROI in the simulation experiment. The
        outer dictionary is structured as ROI : (model_name, parameters). The 'parameters' is a dictionary with
        keyword : value pairs of each parameter for the model. However, SLD type parameters are stored as keyword :
        (formula, density) as these are needed to calculate both the sld and attenuation during the generation of
        simulated H0 and H1byH0 images.
    """

    model_defaults = None
    open_roi = None
    models = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.model_defaults = self.load_model_defaults()
        # self.open_roi = self.find_open_roi()
        # self.models = self.setup_models()

    def load_model_defaults(self):
        """Loads the required defaults from sasmodels_defaults for any models specified in the configuration."""

        model_defaults = {}

        models = list(set(self.__getitem__("model_name")))
        models = [x.split(":")[1].split(",") if "GROUP" in x else [x] for x in models]
        models = [model_name_interpreter(x[0])[3] for x in models]
        models = [x for sublist in models for x in sublist]
        models.extend(["common"])  # scale and background found in "common"
        defaults_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sasmodels_defaults')
        available_models = [x.split('.')[0] for x in os.listdir(defaults_path) if x.split('.')[-1] == 'json']

        # check for models not available
        for model in models:
            if model != "all" and model not in available_models:
                raise Exception(f"Model {model} is not an available model.")
        # check for random model mode keywords
        if 'all' in models:
            models = available_models
        # TODO: implement model groups, e.g. spherical, and their appropriate keywords
        else:
            models = [x for x in models if x in available_models]
            if len(models) == 0:
                print("No recognizable models found in the simulation experiment.")
                raise
        for model in models:
            with open(os.path.join(defaults_path, f'{model}.json')) as file:
                model_defaults[model] = json.load(file)[model]
                file.close()

        return model_defaults

    def find_open_roi(self):
        """Finds the ROI specified as the background or open beam region of the sample image."""

        model_info = self.config["models"]
        open_roi = []
        for model in model_info:
            if model["intent"] == "open":
                open_roi.append(model["roi"])
        open_roi = [x for sublist in open_roi for x in sublist]
        return open_roi

    def get_model_draw_group(self, model_name, roi):

        if model_name == "all":
            model_group = [x for x in list(self.model_defaults.keys()) if x != "common"]
        elif "GROUP:" in model_name:
            model_group = model_name.split(':')[1]
            model_group = model_group.split(',')
            for model in model_group:
                if model not in self.model_defaults.keys():
                    print(f"Model {model} not in accessible SasView models for ROI {roi}.")
                    raise
        else:
            raise Exception(f"Cannot understand model_name {model_name} in 'random' model mode for ROIs {roi}.")

        if len(model_group) >= 1:
            return model_group
        else:
            raise Exception(f"Insufficient amount of models available for random model choice for ROIs {roi}.")

    def gen_random_model(self, random_dict):
        """
        Converts a single 'random' model_mode dictionary for a group of ROI's into a list of dictionaries, one
        for each ROI, with the random model selected to fit in with the standard 'user-defined' model handling
        procedures in setup_models().
        """

        model_name = random_dict["model"]["model_name"]
        roi = random_dict["roi"]

        model_group = self.get_model_draw_group(model_name, roi)
        model_draws = np.random.choice(model_group, size=len(roi), replace=True)

        random_list = []
        for r, model_name in zip(roi, model_draws):
            new_dict = random_dict.copy()
            new_dict["roi"] = [r]
            new_dict["model"]["model_name"] = model_name
            new_dict["model"]["model_mode"] = "user-defined"
            new_dict["model"]["model_parts"][0]["part_name"] = model_name
            random_list.append(new_dict)

        return random_list

    def setup_models(self):
        """
        Returns dictionary of the SasView/sasmodels model and the parameters for each ROI in the simulation experiment.
        The outer dictionary is structured as ROI : (model_name, parameters). The 'parameters' is a dictionary with
        keyword : value pairs of each parameter for the model. However, SLD type parameters are stored as keyword :
        (formula, density, volume fraction) as these are needed to calculate both the sld and attenuation during the
        generation of simulated H0 and H1byH0 images.
        """

        self.model_defaults = self.load_model_defaults()
        self.open_roi = self.find_open_roi()

        model_info = self.config["models"]
        # gen_random_model returns a list of dictionaries for each ROI which is why the [x] and sublist handling is
        # performed here in this way TODO: simplify this approach
        model_info = [
            self.gen_random_model(x) if "model" in x and x["model"]["model_mode"] == "random" else [x]
            for x in model_info]
        model_info = [x for sublist in model_info for x in sublist]

        models = {}
        for model in model_info:

            if model["intent"] == "sample":

                roi = model["roi"]
                n_roi = len(roi)

                model_mode = model["model"]["model_mode"]
                if model_mode != 'user-defined':  # this will change with additional model-modes in the future
                    raise ValueError(f"Unrecognized model_mode {model_mode} for ROI {roi}.")

                model_name, model_name_parts, sasmodel_name, sasmodel_name_parts, prefix, operators = \
                    model_name_interpreter(model["model"]["model_name"])

                model_parts = get_model_parts(model)

                is_structure_factor = has_structure_factor(sasmodel_name)

                # common parameters first
                combined_parameters = {
                    "scale": [1] * n_roi,
                    "background": [0] * n_roi,
                }

                for name, sname, p in zip(model_name_parts, sasmodel_name_parts, prefix):
                    # check that the models provided are implemented into correlogram-tools
                    if sname not in self.model_defaults.keys():
                        raise ValueError(f"Unaccepted model type {name} for ROIs {roi}.")
                    # apply the appropriate prefix to the model parameters excluding sld parameters and background
                    param_list = self.model_defaults[sname].keys()
                    for param in [x for x in param_list if 'sld' not in x and 'background' not in x]:
                        if param in model_parts[name]["parameters"]:
                            param_mode = model_parts[name]["parameters"][param]["parameter_mode"]
                            param_value = model_parts[name]["parameters"][param]["value"]
                        elif param == "scale":
                            param_mode = "user-defined"
                            param_value = [self.model_defaults[sname]["scale"]["value"]]
                        elif "pd" in param:
                            param_mode = "user-defined"
                            param_value = [self.model_defaults[sname][param]["value"]]
                        elif "radius_effective_mode" in param:
                            param_mode = "user-defined"
                            param_value = [self.model_defaults[sname][param]["value"]]
                        else:
                            param_mode = "random-single"
                            param_value = [self.model_defaults[sname][param]["min"],
                                           self.model_defaults[sname][param]["max"]]
                        combined_parameters[p + param] = param_interpreter(param_mode, param_value, n_roi)

                    sld_params = [x for x in param_list if 'sld' in x]
                    for sld_param in sld_params:
                        try:
                            component = model_parts[name]["sample_components"][sld_param]
                            formula, density = component_interpreter(component)
                            volume_fractions = smvolumes.get_volume_fractions(sname, p, sld_param, combined_parameters)

                            combined_parameters[p + sld_param] = [
                                (formula, density, vf) for vf in volume_fractions
                            ]
                        except KeyError:
                            print(model_parts[name]["sample_components"])
                            print(f"Missing {sld_param} in sample_components of {name} in {model_name}.")
                            raise
                        except Exception as e:
                            print(f"Error in reading {sld_param} information for {model_name} model of ROIs {roi}.")
                            raise
                if is_structure_factor:
                    sld_params = [x for x in combined_parameters.keys() if "sld" in x and "solvent" not in x]
                    for sld_param in sld_params:
                        original_params = combined_parameters[sld_param]
                        new_params = []
                        volfraction = combined_parameters["volfraction"]
                        for (formula, density, vf), vf2 in zip(original_params, volfraction):
                            new_params.append((formula, density, vf*vf2))
                        combined_parameters[sld_param] = new_params

                # for a '*' operator the scale terms need to be combined, e.g., A_scale*B_scale = C_scale
                prefix_tracker = ""
                scale_tracker = np.ones_like(roi, dtype=float)
                for i, op in enumerate(operators):
                    if op != '*':
                        if len(prefix_tracker) > 0:
                            prefix_i = prefix[i]
                            prefix_tracker += prefix_i[:-1]
                            scale_i = np.array(combined_parameters.pop(prefix_i+"scale"))
                            scale_tracker *= scale_i
                            combined_parameters[prefix_tracker + '_scale'] = list(scale_tracker)
                        prefix_tracker = ""
                        scale_tracker = np.ones_like(roi, dtype=float)
                    elif op == '*' and i < len(operators)-1:
                        prefix_i = prefix[i]
                        scale_i = np.array(combined_parameters.pop(prefix_i+"scale"))
                        prefix_tracker += prefix_i[:-1]
                        scale_tracker *= scale_i
                    else:
                        prefix_i = prefix[i]
                        scale_i = np.array(combined_parameters.pop(prefix_i + "scale"))
                        prefix_tracker += prefix_i[:-1]
                        scale_tracker *= scale_i
                        # last model in the list
                        prefix_i = prefix[i+1]
                        scale_i = np.array(combined_parameters.pop(prefix_i + "scale"))
                        prefix_tracker += prefix_i[:-1]
                        scale_tracker *= scale_i
                        combined_parameters[prefix_tracker + '_scale'] = list(scale_tracker)

                for i, r in enumerate(roi):
                    r_params = {param: val[i] for param, val in combined_parameters.items()}
                    models[r] = (sasmodel_name, r_params)

            elif model["intent"] == "open":
                pass

            else:
                raise ValueError(f"Model intent {model['intent']} unrecognizable for ROI {model['roi']}.")

        self.models = models
        return models
