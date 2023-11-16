import os
import unittest

import numpy as np
import json

from correlogram_tools import sim_models
from correlogram_tools.sim_models import SimModels


class TestSimModels(unittest.TestCase):

    def setUp(self):
        self.test_config = {}
        self.config_path = os.path.abspath("./test_config.json")
        self.sim_models = SimModels(config_dict=self.test_config, config_path=self.config_path)

    def test_has_structure_factor(self):
        self.assertTrue(sim_models.has_structure_factor("sphere@hardsphere"))
        self.assertTrue(sim_models.has_structure_factor("hardsphere"))
        self.assertFalse(sim_models.has_structure_factor("sphere"))

    def test_random_values_size1(self):
        value = sim_models.random_values(1, 1, 10)[0]
        self.assertLessEqual(value, 10)
        self.assertGreaterEqual(value, 1)

    def test_random_values_sizeN(self):
        n = 5
        value = np.array(sim_models.random_values(n, 1, 10))
        self.assertLessEqual(np.max(value-10), 0)
        self.assertGreaterEqual(np.min(value-1), 0)

    def test_param_interpreter_range(self):
        check_values = sim_models.param_interpreter("range", [1, 5, 5, "linear"], 5)
        true_values = [1, 2, 3, 4, 5]
        self.assertEqual(list(check_values), true_values)

    def test_param_interpreter_user_defined(self):
        check_values = sim_models.param_interpreter("user-defined", [1, 2, 3], 3)
        true_values = [1, 2, 3]
        self.assertEqual(list(check_values), true_values)

    def test_param_interpreter_random(self):
        check_values = sim_models.param_interpreter("random", [1, 10], 3)
        self.assertLessEqual(np.max(np.array(check_values)-10), 0)
        self.assertGreaterEqual(np.min(np.array(check_values)-1), 0)
        self.assertEqual(len(check_values), 3)

    def test_param_interpreter_random_single(self):
        check_values = sim_models.param_interpreter("random-single", [1, 10], 3)
        self.assertLessEqual(np.max(np.array(check_values) - 10), 0)
        self.assertGreaterEqual(np.min(np.array(check_values) - 1), 0)
        self.assertEqual(len(check_values), 3)
        self.assertEqual(len([x for x in check_values if x == check_values[0]]), 3)

    def test_param_interpreter_invalid_mode(self):
        self.assertRaises(
            Exception,
            sim_models.param_interpreter,
            "not_a_mode",
            [1, 10],
            3
        )

    def test_param_interpreter_nroi_range(self):
        self.assertRaises(
            Exception,
            sim_models.param_interpreter,
            "range",
            [1, 10, 3, "linear"],
            5
        )

    def test_param_interpreter_nroi_user_defined(self):
        self.assertRaises(
            Exception,
            sim_models.param_interpreter,
            "user-defined",
            [1, 2, 3],
            5
        )

    def test_component_interpreter_molecular_formula(self):
        component_dict = {
            "component_mode": "molecular-formula",
            "value": "H2O",
            "density": 1,
        }
        formula, density = sim_models.component_interpreter(component_dict)
        self.assertEqual(formula, "H2O")
        self.assertEqual(density, 1)

    def test_component_interpreter_component_library(self):
        component_dict = {
            "component_mode": "component-library",
            "value": "water",
            "density": 2,
        }
        formula, density = sim_models.component_interpreter(component_dict)
        water_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            os.path.relpath("../correlogram_tools/component_library/water.json")
        )
        with open(water_path) as file:
            water = json.load(file)["water"]
            file.close()
        self.assertEqual(formula, water["formula"])
        self.assertEqual(density, water["density"])

    def test_component_interpreter_unaccepted_keyword(self):
        component_dict = {
            "component_mode": "unaccepted_keyword",
            "value": "water",
            "density": 2,
        }
        self.assertRaises(
            Exception,
            sim_models.component_interpreter,
            component_dict)

    def test_component_interpreter_missing_mode(self):
        component_dict = {
            "value": "water",
            "density": 2,
        }
        self.assertRaises(
            Exception,
            sim_models.component_interpreter,
            component_dict)

    def test_component_interpreter_missing_value(self):
        component_dict = {
            "component_mode": "component-library",
            "density": 2,
        }
        self.assertRaises(
            Exception,
            sim_models.component_interpreter,
            component_dict)

    def test_component_interpreter_missing_density(self):
        component_dict = {
            "component_mode": "molecular-formula",
            "value": "H2O",
        }
        self.assertRaises(
            Exception,
            sim_models.component_interpreter,
            component_dict)

    def test_component_interpreter_unavailable_component(self):
        component_dict = {
            "component_mode": "component-library",
            "value": "not_a_component",
        }
        self.assertRaises(
            Exception,
            sim_models.component_interpreter,
            component_dict)

    def test_model_name_interpreter_same_models(self):
        model_name = "sphere1+sphere2"
        model_name_parts = ["sphere1", "sphere2"]
        sasmodel_name = "sphere+sphere"
        sasmodel_name_parts = ["sphere", "sphere"]
        prefixes = ["A_", "B_"]
        operators = ["+"]

        check_names = sim_models.model_name_interpreter(model_name)
        self.assertEqual(model_name, check_names[0])
        self.assertEqual(model_name_parts, check_names[1])
        self.assertEqual(sasmodel_name, check_names[2])
        self.assertEqual(sasmodel_name_parts, check_names[3])
        self.assertEqual(prefixes, check_names[4])
        self.assertEqual(operators, check_names[5])

    def test_model_name_interpreter_different_models(self):
        model_name = "sphere1+cylinder3"
        model_name_parts = ["sphere1", "cylinder3"]
        sasmodel_name = "sphere+cylinder"
        sasmodel_name_parts = ["sphere", "cylinder"]
        prefixes = ["A_", "B_"]
        operators = ["+"]

        check_names = sim_models.model_name_interpreter(model_name)
        self.assertEqual(model_name, check_names[0])
        self.assertEqual(model_name_parts, check_names[1])
        self.assertEqual(sasmodel_name, check_names[2])
        self.assertEqual(sasmodel_name_parts, check_names[3])
        self.assertEqual(prefixes, check_names[4])
        self.assertEqual(operators, check_names[5])

    def test_model_name_interpreter_structure_factor(self):
        model_name = "sphere1@hardsphere2"
        model_name_parts = ["sphere1", "hardsphere2"]
        sasmodel_name = "sphere@hardsphere"
        sasmodel_name_parts = ["sphere", "hardsphere"]
        prefixes = ["", ""]
        operators = ["@"]

        check_names = sim_models.model_name_interpreter(model_name)
        self.assertEqual(model_name, check_names[0])
        self.assertEqual(model_name_parts, check_names[1])
        self.assertEqual(sasmodel_name, check_names[2])
        self.assertEqual(sasmodel_name_parts, check_names[3])
        self.assertEqual(prefixes, check_names[4])
        self.assertEqual(operators, check_names[5])

    def test_model_name_interpreter_structure_factor_incorrect_format(self):
        model_name = "hardsphere@hardsphere2"
        self.assertRaises(Exception, sim_models.model_name_interpreter, model_name)

        model_name = "sphere@sphere"
        self.assertRaises(Exception, sim_models.model_name_interpreter, model_name)

        model_name = "sphere@hardsphere@hardsphere"
        self.assertRaises(Exception, sim_models.model_name_interpreter, model_name)

    def test_model_name_interpreter_single_model(self):
        model_name = "sphere"
        model_name_parts = ["sphere"]
        sasmodel_name = "sphere"
        sasmodel_name_parts = ["sphere"]
        prefixes = [""]
        operators = []
        check_names = sim_models.model_name_interpreter(model_name)
        self.assertEqual(model_name, check_names[0])
        self.assertEqual(model_name_parts, check_names[1])
        self.assertEqual(sasmodel_name, check_names[2])
        self.assertEqual(sasmodel_name_parts, check_names[3])
        self.assertEqual(prefixes, check_names[4])
        self.assertEqual(operators, check_names[5])

    def test_model_name_interpreter_combination(self):
        model_name = "sphere1+cylinder*sphere2+cylinder2+ellipsoid4*ellipsoid3*sphere4"
        model_name_parts = ["sphere1", "cylinder", "sphere2", "cylinder2", "ellipsoid4", "ellipsoid3", "sphere4"]
        sasmodel_name = "sphere+cylinder*sphere+cylinder+ellipsoid*ellipsoid*sphere"
        sasmodel_name_parts = ["sphere", "cylinder", "sphere", "cylinder", "ellipsoid", "ellipsoid", "sphere"]
        prefixes = ["F_", "A_", "B_", "G_", "C_", "D_", "E_"]
        operators = ["+", "*", "+", "+", "*", "*"]
        check_names = sim_models.model_name_interpreter(model_name)
        self.assertEqual(model_name, check_names[0])
        self.assertEqual(model_name_parts, check_names[1])
        self.assertEqual(sasmodel_name, check_names[2])
        self.assertEqual(sasmodel_name_parts, check_names[3])
        self.assertEqual(prefixes, check_names[4])
        self.assertEqual(operators, check_names[5])

    def test_get_model_parts(self):
        test_model = {
            "roi": [1, 2, 3],
            "intent": "sample",
            "model": {
                "model_mode": "user-defined",
                "model_name": "sphere1+sphere3",
                "model_parts": [
                    {
                        "part_name": "sphere1",
                        "parameters": {
                            "radius": {"parameter_mode": "user-defined", "value": [200]},
                            "scale": {"parameter_mode": "user-defined", "value": [0.05, 0.10, 0.15]}
                        },
                        "sample_components": {
                            "solute": {
                                "component_mode": "molecular-formula",
                                "value": "C8H8",
                                "density": 1.01,
                            },
                            "solvent": {
                                "component_mode": "component-library",
                                "value": "deuterium_oxide.json"
                            }
                        }
                    },
                    {
                        "part_name": "sphere3",
                        "parameters": {
                            "radius": {"parameter_mode": "user-defined", "value": [100]},
                            "scale": {"parameter_mode": "user-defined", "value": [0.05, 0.10, 0.15]}
                        },
                        "sample_components": {
                            "solute": {
                                "component_mode": "molecular-formula",
                                "value": "C8H8",
                                "density": 1.01,
                            },
                            "solvent": {
                                "component_mode": "component-library",
                                "value": "deuterium_oxide.json"
                            }
                        }
                    }
                ]
            }
        }
        model_parts = sim_models.get_model_parts(test_model)
        self.assertCountEqual(list(model_parts.keys()), ["sphere1", "sphere3"])

        parameters_sphere1 = test_model["model"]["model_parts"][0]["parameters"]
        if not model_parts["sphere1"]["parameters"] == parameters_sphere1:
            raise Exception("Parameters for sphere1 in model_parts does not match given model dictionary.")

        parameters_sphere3 = test_model["model"]["model_parts"][1]["parameters"]
        if not model_parts["sphere3"]["parameters"] == parameters_sphere3:
            raise Exception("Parameters for sphere3 in model_parts does not match given model dictionary.")

        components_sphere1 = test_model["model"]["model_parts"][0]["sample_components"]
        if not model_parts["sphere1"]["sample_components"] == components_sphere1:
            raise Exception("Components for sphere1 in model_parts does not match given model dictionary.")

        components_sphere3 = test_model["model"]["model_parts"][1]["sample_components"]
        if not model_parts["sphere3"]["sample_components"] == components_sphere3:
            raise Exception("Components for sphere3 in model_parts does not match given model dictionary.")

    def test_get_model_parts_missing_parameters(self):
        test_model = {
            "roi": [1, 2, 3],
            "intent": "sample",
            "model": {
                "model_mode": "user-defined",
                "model_name": "sphere1+sphere3",
                "model_parts": [
                    {
                        "part_name": "sphere1",
                        "parameters": {
                            "radius": {"parameter_mode": "user-defined", "value": [200]},
                            "scale": {"parameter_mode": "user-defined", "value": [0.05, 0.10, 0.15]}
                        },
                        "sample_components": {
                            "solute": {
                                "component_mode": "molecular-formula",
                                "value": "C8H8",
                                "density": 1.01,
                            },
                            "solvent": {
                                "component_mode": "component-library",
                                "value": "deuterium_oxide.json"
                            }
                        }
                    },
                    {
                        "part_name": "sphere3",
                        "sample_components": {
                            "solute": {
                                "component_mode": "molecular-formula",
                                "value": "C8H8",
                                "density": 1.01,
                            },
                            "solvent": {
                                "component_mode": "component-library",
                                "value": "deuterium_oxide.json"
                            }
                        }
                    }
                ]
            }
        }
        model_parts = sim_models.get_model_parts(test_model)
        self.assertCountEqual(list(model_parts.keys()), ["sphere1", "sphere3"])

        parameters_sphere1 = test_model["model"]["model_parts"][0]["parameters"]
        if not model_parts["sphere1"]["parameters"] == parameters_sphere1:
            raise Exception("Parameters for sphere1 in model_parts does not match given model dictionary.")

        if not model_parts["sphere3"]["parameters"] == {}:
            raise Exception("Parameters for sphere3 in model_parts does not match given model dictionary.")

        components_sphere1 = test_model["model"]["model_parts"][0]["sample_components"]
        if not model_parts["sphere1"]["sample_components"] == components_sphere1:
            raise Exception("Components for sphere1 in model_parts does not match given model dictionary.")

        components_sphere3 = test_model["model"]["model_parts"][1]["sample_components"]
        if not model_parts["sphere3"]["sample_components"] == components_sphere3:
            raise Exception("Components for sphere3 in model_parts does not match given model dictionary.")

    def test_get_model_parts_missing_sample_components(self):
        test_model = {
            "roi": [1, 2, 3],
            "intent": "sample",
            "model": {
                "model-mode": "user-defined",
                "model-name": "sphere1+sphere3",
                "model-parts": [
                    {
                        "part-name": "sphere1",
                        "parameters": {
                            "radius": {"parameter_mode": "user-defined", "value": [200]},
                            "scale": {"parameter_mode": "user-defined", "value": [0.05, 0.10, 0.15]}
                        },
                    },
                    {
                        "part-name": "sphere3",
                        "parameters": {
                            "radius": {"parameter_mode": "user-defined", "value": [100]},
                            "scale": {"parameter_mode": "user-defined", "value": [0.05, 0.10, 0.15]}
                        },
                        "sample_components": {
                            "solute": {
                                "component_mode": "molecular-formula",
                                "value": "C8H8",
                                "density": 1.01,
                            },
                            "solvent": {
                                "component_mode": "component-library",
                                "value": "deuterium_oxide.json"
                            }
                        }
                    }
                ]
            }
        }
        self.assertRaises(
            Exception,
            sim_models.get_model_parts,
            test_model
        )

    # def test_get_prefix_list(self):
    #     model_name_parts = ["sphere1", "cylinder3", "sphere2", "random4"]
    #     prefix = sim_models.get_prefix_list(model_name_parts)
    #     self.assertEqual(["A_", "B_", "C_", "D_"], prefix)
    #
    # def test_get_prefix_list_single(self):
    #     model_name_parts = ["sphere6"]
    #     prefix = sim_models.get_prefix_list(model_name_parts)
    #     self.assertEqual([""], prefix)
    #
    # def test_get_prefix_list_too_long(self):
    #     model_name_parts = ["sphere"]*27
    #     self.assertRaises(
    #         Exception,
    #         sim_models.get_prefix_list,
    #         model_name_parts
    #     )

    def test_load_model_defaults(self):
        test_dict = {
            "model-name": "sphere",
            "another_model": {"model_name": "sphere"},
            "a_third_model": {"model_name": "sphere"}
        }
        self.sim_models.config = test_dict
        model_defaults = self.sim_models.load_model_defaults()
        self.assertCountEqual(["common", "sphere"], list(model_defaults.keys()))

    def test_load_model_defaults_all(self):
        test_dict = {
            "model-name": "sphere",
            "another_model": {"model_name": "all"},
            "a_third_model": {"model_name": "sphere"}
        }
        self.sim_models.config = test_dict
        sasmodels_defaults = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            os.path.relpath("../correlogram_tools/sasmodels_defaults")
        )
        all_models = [x.split('.')[0] for x in os.listdir(sasmodels_defaults) if x.split('.')[-1] == 'json']
        model_defaults = self.sim_models.load_model_defaults()
        self.assertCountEqual(all_models, list(model_defaults.keys()))

    def test_load_model_defaults_group(self):
        test_dict = {
            "another_model": {"model_name": "GROUP:sphere"},
        }
        self.sim_models.config = test_dict
        model_defaults = self.sim_models.load_model_defaults()
        self.assertCountEqual(["sphere", "common"], list(model_defaults.keys()))

    def test_load_model_defaults_numbered(self):
        test_dict = {
            "model-name": "sphere3",
            "another_model": {"model_name": "GROUP:sphere"},
            "a_third_model": {"model_name": "sphere3"}
        }
        self.sim_models.config = test_dict
        model_defaults = self.sim_models.load_model_defaults()
        self.assertCountEqual(["sphere", "common"], list(model_defaults.keys()))

    def test_load_model_defaults_combined(self):
        test_dict = {
            "model_name": "sphere+sphere",
        }
        self.sim_models.config = test_dict
        model_defaults = self.sim_models.load_model_defaults()
        self.assertCountEqual(["sphere", "common"], list(model_defaults.keys()))

    def test_load_model_defaults_unknown_model(self):
        test_dict = {
            "model_name": "sphere+sphere",
            "another_model": {"model_name": "GROUP:sphere"},
            "a_third_model": {"model_name": "not_a_model"}
        }
        self.sim_models.config = test_dict
        self.assertRaises(
            Exception,
            self.sim_models.load_model_defaults
        )

    def test_find_open_roi(self):
        test_config = {
            "models": [
                {"intent": "open", "roi": [1]},
                {"intent": "sample", "roi": [2, 3]},
                {"intent": "open", "roi": [4, 5, 6]}
            ]
        }
        self.sim_models.config = test_config
        self.assertEqual([1, 4, 5, 6], self.sim_models.find_open_roi())

    def test_get_model_draw_group_all(self):
        # make sure the model defaults are available for this test
        test_config = {
            "model_name": "all",
            "another": {"model_name": "GROUP:sphere"}
        }
        self.sim_models.config = test_config
        self.sim_models.model_defaults = self.sim_models.load_model_defaults()

        model_group = self.sim_models.get_model_draw_group("all", [1, 2, 3])
        sasmodels_defaults = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            os.path.relpath("../correlogram_tools/sasmodels_defaults")
        )
        all_models = [x.split('.')[0] for x in os.listdir(sasmodels_defaults) if "common" not in x]
        self.assertEqual(model_group, all_models)


    def test_get_model_draw_group_group(self):
        # TODO: this test will become more relevant when there are more than sphere models available
        # make sure the model defaults are available for this test
        test_config = {
            "model_name": "all",
            "another": {"model_name": "GROUP:sphere"}
        }
        self.sim_models.config = test_config
        self.sim_models.model_defaults = self.sim_models.load_model_defaults()

        model_group = self.sim_models.get_model_draw_group("GROUP:sphere", [1, 2, 3])
        self.assertEqual(model_group, ["sphere"])

    def test_get_model_draw_group_invalid_model(self):
        # TODO: this test will become more relevant when there are more than sphere models available
        # make sure the model defaults are available for this test
        test_config = {
            "model_name": "all",
            "another": {"model_name": "sphere"}
        }
        self.sim_models.config = test_config
        self.sim_models.model_defaults = self.sim_models.load_model_defaults()

        self.assertRaises(
            Exception,
            self.sim_models.get_model_draw_group,
            "not_a_model",
            [1, 2, 3]
        )

    def test_gen_random_model(self):
        # make sure the model defaults are available for this test
        test_config = {
            "model_name": "all",
            "another": {"model_name": "GROUP:sphere"}
        }
        self.sim_models.config = test_config
        self.sim_models.model_defaults = self.sim_models.load_model_defaults()

        test_random_dict = {
            "roi": [1, 2, 3],
            "intent": "sample",
            "model": {
                "model_mode": "random",
                "model_name": "GROUP:sphere",
                "model_parts": [
                    {
                        "part_name": "random",
                        "parameters": {},
                        "sample_components": {"solute": {}, "solvent": {}}
                    }
                ]
            }
        }
        random_list = self.sim_models.gen_random_model(test_random_dict)

        rois = [x["roi"] for x in random_list]
        self.assertEqual(rois, [[1], [2], [3]])

        intents = [x["intent"] for x in random_list]
        self.assertEqual(intents, ["sample"]*3)

        model_modes = [x["model"]["model_mode"] for x in random_list]
        self.assertEqual(model_modes, ["user-defined"]*3)

        model_names = [x["model"]["model_name"] for x in random_list]
        self.assertEqual(model_names, ["sphere"]*3)

    def test_setup_models(self):

        test_config = {
            "models": [
                {
                    "roi": [4],
                    "intent": "open",
                },
                {
                    "roi": [1, 2],
                    "intent": "sample",
                    "model": {
                        "model_mode": "random",
                        "model_name": "GROUP:sphere",
                        "model_parts": [
                            {
                                "part_name": "random",
                                "parameters": {},
                                "sample_components": {
                                    "sld": {
                                        "component_mode": "molecular-formula",
                                        "value": "C8H8",
                                        "density": 1.01,
                                    },
                                    "sld_solvent": {
                                        "component_mode": "component-library",
                                        "value": "deuterium_oxide.json"
                                    }
                                }
                            }
                        ]
                    }
                },
                {
                    "roi": [3, 5, 6],
                    "intent": "sample",
                    "model": {
                        "model_mode": "user-defined",
                        "model_name": "sphere1+sphere3",
                        "model_parts": [
                            {
                                "part_name": "sphere1",
                                "parameters": {
                                    "radius": {"parameter_mode": "user-defined", "value": [200]},
                                    "radius_pd": {"parameter_mode": "user-defined", "value": [0.1]},
                                    "scale": {"parameter_mode": "user-defined", "value": [0.05, 0.10, 0.15]}
                                },
                                "sample_components": {
                                    "sld": {
                                        "component_mode": "molecular-formula",
                                        "value": "C8H8",
                                        "density": 1.01,
                                    },
                                    "sld_solvent": {
                                        "component_mode": "component-library",
                                        "value": "deuterium_oxide.json"
                                    }
                                }
                            },
                            {
                                "part_name": "sphere3",
                                "parameters": {
                                    "radius": {"parameter_mode": "user-defined", "value": [100]},
                                    "scale": {"parameter_mode": "user-defined", "value": [0.05, 0.10, 0.20]}
                                },
                                "sample_components": {
                                    "sld": {
                                        "component_mode": "molecular-formula",
                                        "value": "C8H8",
                                        "density": 1.01,
                                    },
                                    "sld_solvent": {
                                        "component_mode": "component-library",
                                        "value": "deuterium_oxide.json"
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }

        self.sim_models.config = test_config
        models = self.sim_models.setup_models()

        open_roi = 4
        if open_roi in models.keys():
            raise Exception("Open ROI was not removed from the models dictionary during model setup.")

        random_parameters = ["scale", "background", "radius", "radius_pd", "radius_pd_n", "radius_pd_nsigma",
                             "radius_pd_type", "sld", "sld_solvent"]
        self.assertCountEqual(list(models[1][1].keys()), random_parameters)
        self.assertCountEqual(list(models[2][1].keys()), random_parameters)
        if models[1][1]["sld"] != models[2][1]["sld"]:
            raise Exception("Sample components did not get copied correctly to ROI 1 and 2 in the model group.")
        if models[1][1]["sld_solvent"] != models[2][1]["sld_solvent"]:
            raise Exception("Sample components did not get copied correctly to ROI 1 and 2 in the model group.")

        sphere_sphere_parameters = [
            "scale", "background",
            "A_scale", "A_radius", "A_sld", "A_sld_solvent",
            "A_radius_pd", "A_radius_pd_n", "A_radius_pd_nsigma", "A_radius_pd_type",
            "B_scale", "B_radius", "B_sld", "B_sld_solvent",
            "B_radius_pd", "B_radius_pd_n", "B_radius_pd_nsigma", "B_radius_pd_type",
        ]
        self.assertCountEqual(list(models[3][1].keys()), sphere_sphere_parameters)
        self.assertCountEqual(list(models[5][1].keys()), sphere_sphere_parameters)
        self.assertCountEqual(list(models[6][1].keys()), sphere_sphere_parameters)

        # confirm that the polydispersity values were applied correctly
        self.assertEqual(models[5][1]["A_radius_pd"], 0.1)
        self.assertEqual(models[5][1]["B_radius_pd"], 0)

        # confirm that standard parameters were applied correctly
        self.assertEqual(models[5][1]["A_radius"], 200)
        self.assertEqual(models[5][1]["B_radius"], 100)

    def test_setup_models_complex_model(self):

        test_config = {
            "models": [
                {
                    "roi": [4],
                    "intent": "open",
                },
                {
                    "roi": [3, 5, 6],
                    "intent": "sample",
                    "model": {
                        "model_mode": "user-defined",
                        "model_name": "sphere1+sphere2*sphere3*sphere4+sphere5+sphere6*sphere7",
                        "model_parts": [
                            {
                                "part_name": "sphere1",
                                "parameters": {
                                    "radius": {"parameter_mode": "user-defined", "value": [200]},
                                    "radius_pd": {"parameter_mode": "user-defined", "value": [0.1]},
                                    "scale": {"parameter_mode": "user-defined", "value": [0.05, 0.10, 0.15]}
                                },
                                "sample_components": {
                                    "sld": {
                                        "component_mode": "molecular-formula",
                                        "value": "C8H8",
                                        "density": 1.01,
                                    },
                                    "sld_solvent": {
                                        "component_mode": "component-library",
                                        "value": "deuterium_oxide.json"
                                    }
                                }
                            },
                            {
                                "part_name": "sphere2",
                                "parameters": {
                                    "radius": {"parameter_mode": "user-defined", "value": [100]},
                                    "scale": {"parameter_mode": "user-defined", "value": [0.05, 0.10, 0.15]}
                                },
                                "sample_components": {
                                    "sld": {
                                        "component_mode": "molecular-formula",
                                        "value": "C8H8",
                                        "density": 1.01,
                                    },
                                    "sld_solvent": {
                                        "component_mode": "component-library",
                                        "value": "deuterium_oxide.json"
                                    }
                                }
                            },
                            {
                                "part_name": "sphere3",
                                "parameters": {
                                    "radius": {"parameter_mode": "user-defined", "value": [100]},
                                    "scale": {"parameter_mode": "user-defined", "value": [0.5, 0.5, 0.5]}
                                },
                                "sample_components": {
                                    "sld": {
                                        "component_mode": "molecular-formula",
                                        "value": "C8H8",
                                        "density": 1.01,
                                    },
                                    "sld_solvent": {
                                        "component_mode": "component-library",
                                        "value": "deuterium_oxide.json"
                                    }
                                }
                            },
                            {
                                "part_name": "sphere4",
                                "parameters": {
                                    "radius": {"parameter_mode": "user-defined", "value": [100]},
                                    "scale": {"parameter_mode": "user-defined", "value": [3, 3, 3]}
                                },
                                "sample_components": {
                                    "sld": {
                                        "component_mode": "molecular-formula",
                                        "value": "C8H8",
                                        "density": 1.01,
                                    },
                                    "sld_solvent": {
                                        "component_mode": "component-library",
                                        "value": "deuterium_oxide.json"
                                    }
                                }
                            },
                            {
                                "part_name": "sphere5",
                                "parameters": {
                                    "radius": {"parameter_mode": "user-defined", "value": [100]},
                                    "scale": {"parameter_mode": "user-defined", "value": [0.1, 0.1, 0.1]}
                                },
                                "sample_components": {
                                    "sld": {
                                        "component_mode": "molecular-formula",
                                        "value": "C8H8",
                                        "density": 1.01,
                                    },
                                    "sld_solvent": {
                                        "component_mode": "component-library",
                                        "value": "deuterium_oxide.json"
                                    }
                                }
                            },
                            {
                                "part_name": "sphere6",
                                "parameters": {
                                    "radius": {"parameter_mode": "user-defined", "value": [100]},
                                    "scale": {"parameter_mode": "user-defined", "value": [1, 1, 1]}
                                },
                                "sample_components": {
                                    "sld": {
                                        "component_mode": "molecular-formula",
                                        "value": "C8H8",
                                        "density": 1.01,
                                    },
                                    "sld_solvent": {
                                        "component_mode": "component-library",
                                        "value": "deuterium_oxide.json"
                                    }
                                }
                            },
                            {
                                "part_name": "sphere7",
                                "parameters": {
                                    "radius": {"parameter_mode": "user-defined", "value": [100]},
                                    "scale": {"parameter_mode": "user-defined", "value": [0.001, 0.002, 0.003]}
                                },
                                "sample_components": {
                                    "sld": {
                                        "component_mode": "molecular-formula",
                                        "value": "C8H8",
                                        "density": 1.01,
                                    },
                                    "sld_solvent": {
                                        "component_mode": "component-library",
                                        "value": "deuterium_oxide.json"
                                    }
                                }
                            },
                        ]
                    }
                }
            ]
        }

        self.sim_models.config = test_config
        models = self.sim_models.setup_models()

        open_roi = 4
        if open_roi in models.keys():
            raise Exception("Open ROI was not removed from the models dictionary during model setup.")

        parameters = [
            "scale", "background",
            "ABC_scale", "A_radius", "A_sld", "A_sld_solvent",
            "A_radius_pd", "A_radius_pd_n", "A_radius_pd_nsigma", "A_radius_pd_type",
            "B_radius", "B_sld", "B_sld_solvent",
            "B_radius_pd", "B_radius_pd_n", "B_radius_pd_nsigma", "B_radius_pd_type",
            "C_radius", "C_sld", "C_sld_solvent",
            "C_radius_pd", "C_radius_pd_n", "C_radius_pd_nsigma", "C_radius_pd_type",
            "DE_scale", "D_radius", "D_sld", "D_sld_solvent",
            "D_radius_pd", "D_radius_pd_n", "D_radius_pd_nsigma", "D_radius_pd_type",
            "E_radius", "E_sld", "E_sld_solvent",
            "E_radius_pd", "E_radius_pd_n", "E_radius_pd_nsigma", "E_radius_pd_type",
            "F_scale", "F_radius", "F_sld", "F_sld_solvent",
            "F_radius_pd", "F_radius_pd_n", "F_radius_pd_nsigma", "F_radius_pd_type",
            "G_scale", "G_radius", "G_sld", "G_sld_solvent",
            "G_radius_pd", "G_radius_pd_n", "G_radius_pd_nsigma", "G_radius_pd_type",
        ]
        self.assertCountEqual(list(models[3][1].keys()), parameters)
        self.assertCountEqual(list(models[5][1].keys()), parameters)
        self.assertCountEqual(list(models[6][1].keys()), parameters)

        # confirm that the common scales were applied correctly
        self.assertEqual(models[3][1]["scale"], 1)
        self.assertEqual(models[5][1]["scale"], 1)
        self.assertEqual(models[6][1]["scale"], 1)

        # confirm scale values for roi 3
        self.assertAlmostEqual(models[3][1]["F_scale"], 0.05, places=5)
        self.assertAlmostEqual(models[3][1]["ABC_scale"], 0.075, places=5)
        self.assertAlmostEqual(models[3][1]["G_scale"], 0.1, places=5)
        self.assertAlmostEqual(models[3][1]["DE_scale"], 0.001, places=5)

        # confirm scale values for roi 5
        self.assertAlmostEqual(models[5][1]["F_scale"], 0.1, places=5)
        self.assertAlmostEqual(models[5][1]["ABC_scale"], 0.15, places=5)
        self.assertAlmostEqual(models[5][1]["G_scale"], 0.1, places=5)
        self.assertAlmostEqual(models[5][1]["DE_scale"], 0.002, places=5)

        # confirm scale values for roi 6
        self.assertAlmostEqual(models[6][1]["F_scale"], 0.15, places=5)
        self.assertAlmostEqual(models[6][1]["ABC_scale"], 0.225, places=5)
        self.assertAlmostEqual(models[6][1]["G_scale"], 0.1, places=5)
        self.assertAlmostEqual(models[6][1]["DE_scale"], 0.003, places=5)

    def test_setup_models_wrong_model_intent(self):

        test_config = {
            "models": [
                {
                    "roi": [4],
                    "intent": "unaccepted_intent",
                },
                {
                    "roi": [1, 2],
                    "intent": "sample",
                    "model": {
                        "model-mode": "random",
                        "model-name": "GROUP:sphere",
                        "model-parts": [
                            {
                                "part-name": "random",
                                "parameters": {},
                                "sample_components": {
                                    "solute": {
                                        "component_mode": "molecular-formula",
                                        "value": "C8H8",
                                        "density": 1.01,
                                    },
                                    "solvent": {
                                        "component_mode": "component-library",
                                        "value": "deuterium_oxide.json"
                                    }
                                }
                            }
                        ]
                    }
                },
                {
                    "roi": [3, 5, 6],
                    "intent": "sample",
                    "model": {
                        "model-mode": "user-defined",
                        "model-name": "sphere1+sphere3",
                        "model-parts": [
                            {
                                "part-name": "sphere1",
                                "parameters": {
                                    "radius": {"parameter_mode": "user-defined", "value": [200]},
                                    "scale": {"parameter_mode": "user-defined", "value": [0.05, 0.10, 0.15]}
                                },
                                "sample_components": {
                                    "solute": {
                                        "component_mode": "molecular-formula",
                                        "value": "C8H8",
                                        "density": 1.01,
                                    },
                                    "solvent": {
                                        "component_mode": "component-library",
                                        "value": "deuterium_oxide.json"
                                    }
                                }
                            },
                            {
                                "part-name": "sphere3",
                                "parameters": {
                                    "radius": {"parameter_mode": "user-defined", "value": [100]},
                                    "scale": {"parameter_mode": "user-defined", "value": [0.05, 0.10, 0.15]}
                                },
                                "sample_components": {
                                    "solute": {
                                        "component_mode": "molecular-formula",
                                        "value": "C8H8",
                                        "density": 1.01,
                                    },
                                    "solvent": {
                                        "component_mode": "component-library",
                                        "value": "deuterium_oxide.json"
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }

        self.sim_models.config = test_config
        self.assertRaises(
            Exception,
            self.sim_models.setup_models,
        )


if __name__ == "__main__":
    unittest.main()
