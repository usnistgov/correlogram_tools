import numpy as np
import periodictable.nsf as nsf
import os
from correlogram_tools import sim_experiment
from correlogram_tools.sim_experiment import SimExperiment
import unittest

def near(a, b):
    return unittest.TestCase.assertAlmostEqual()

class TestSimExperiment(unittest.TestCase):

    def setUp(self):
        self.sim_experiment = SimExperiment(os.path.join(os.path.dirname(__file__),
                                                         os.path.relpath("test_data/test_config.json")))

    def test_mixture_formula(self):
        test_params = {
            "scale": 1,
            "background": 0,
            "A_scale": 0.1,
            "A_sld": ("C8D8", 1.01, 0.1),
            "A_sld_solvent": ("D2O", 1.1, 0.99),
            "B_scale": 0.05,
            "B_sld": ("C8H8", 1.01, 0.05),
            "B_sld_solvent": ("D2O", 1.1, 0.95),
            "B_radius": 200,
        }
        formula = sim_experiment.mixture_formula(test_params)
        true_formula = "10.0%vol C8D8@1.01 // 5.0%vol C8H8@1.01 // D2O@1.1"
        self.assertEqual(formula, true_formula)

    def test_mixture_formula_single_model(self):
        test_params = {
            "scale": 0.1,
            "background": 0,
            "sld": ("C8D8", 1.01, 0.1),
            "sld_solvent": ("D2O", 1.1, 0.99),
        }
        formula = sim_experiment.mixture_formula(test_params)
        true_formula = "10.0%vol C8D8@1.01 // D2O@1.1"
        self.assertEqual(formula, true_formula)

    ## this is not currently an available feature in correlogram-tools, the outer scale is always 1 for combined models
    # def test_mixture_formula_two_scales(self):
    #     test_params = {
    #         "scale": 0.5,
    #         "background": 0,
    #         "A_scale": 0.1,
    #         "A_sld": ("C8D8", 1.01, 0.1),
    #         "A_sld_solvent": ("D2O", 1.1, 0.9),
    #         "B_scale": 0.05,
    #         "B_sld": ("C8H8", 1.01, 0.05),
    #         "B_sld_solvent": ("D2O", 1.1, 0.95),
    #         "B_radius": 200,
    #     }
    #     formula = sim_experiment.mixture_formula(test_params)
    #     true_formula = "5.0%vol C8D8@1.01 // 2.5%vol C8H8@1.01 // D2O@1.1"
    #     self.assertEqual(formula, true_formula)

    def test_gen_penetration_depth(self):
        test_params = {
            "scale": 1,
            "background": 0,
            "A_scale": 0.1,
            "A_sld": ("C8D8", 1.01, 0.1),
            "A_sld_solvent": ("D2O", 1.1, 0.9),
            "B_scale": 0.05,
            "B_sld": ("C8H8", 1.01, 0.05),
            "B_sld_solvent": ("D2O", 1.1, 0.95),
            "B_radius": 200,
        }
        formula = "10.0%vol C8D8@1.01 // 5.0%vol C8H8@1.01 // D2O@1.1"
        wavelength = 0.6

        depth = sim_experiment.get_penetration_depth(test_params, wavelength=wavelength)
        true_depth = nsf.neutron_scattering(formula, wavelength=wavelength*10)[-1]
        self.assertEqual(depth, true_depth)

    def test_compute_sld(self):
        wavelength = 0.6
        test_param_dict = {
            "scale": 0.1,
            "background": 0,
            "radius": 200,
            "sld": ("C8H8", 1.01, 0.1),
            "sld_solvent": ("D2O", 1.1, 0.99)
        }
        test_param_dict_converted = {
            "scale": 0.1,
            "background": 0,
            "radius": 200,
            "sld": nsf.neutron_scattering("C8H8", density=1.01, wavelength=wavelength*10)[0][0],
            "sld_solvent": nsf.neutron_scattering("D2O", density=1.1, wavelength=wavelength*10)[0][0],
        }

        new_params = sim_experiment.compute_sld(test_param_dict, wavelength)
        if new_params != test_param_dict_converted:
            raise Exception("The converted parameter dictionary does not match!")

    def test_apply_pen_mu_per_wavelength(self):

        test_wavelength = 0.3

        self.sim_experiment.measurements_xi = np.array([30, 45, 90, 60, 75])
        self.sim_experiment.measurements_moire = np.array([2, 2, 2, 2, 2])
        self.sim_experiment.measurements_wavelength = np.array([0.2, 0.3, 0.3, 0.4, 0.5])
        self.sim_experiment.measurements_z = np.array([30, 30, 60, 30, 30])

        penetration = np.ones(5)
        mu = np.ones(5)

        model_name = "sphere"
        param_dict = {
            "scale": 0.1,
            "background": 0,
            "radius": 200,
            "sld": ("C8H8", 1.01, 0.1),
            "sld_solvent": ("D2O", 1.1, 0.9)
        }

        check_penetration, check_mu = self.sim_experiment.apply_pen_mu_per_wavelength(
            penetration,
            mu,
            model_name,
            param_dict,
            test_wavelength
        )

        self.assertEqual(list(np.where(check_penetration != 1)[0]), [1, 2])
        self.assertEqual(list(np.where(check_mu != 1)[0]), [1, 2])

    def test_get_penetration_depth_and_correlograms(self):

        self.sim_experiment.measurements_xi = np.array([30, 45, 45, 30, 30])
        self.sim_experiment.measurements_moire = np.array([2, 2, 2, 2, 2])
        self.sim_experiment.measurements_wavelength = np.array([0.2, 0.3, 0.3, 0.2, 0.2])
        self.sim_experiment.measurements_z = np.array([30, 30, 30, 30, 30])

        models = {
            1: (
                "sphere",
                {
                    "scale": 0.1,
                    "background": 0,
                    "radius": 200,
                    "sld": ("C8H8", 1.01, 0.1),
                    "sld_solvent": ("D2O", 1.1, 0.9)
                }
            ),
            2: (
                "sphere",
                {
                    "scale": 0.15,
                    "background": 0,
                    "radius": 100,
                    "sld": ("C8H8", 1.01, 0.15),
                    "sld_solvent": ("D2O", 1.1, 0.85)
                }
            )
        }
        self.sim_experiment.models = models

        penetration_roi, mu_roi = self.sim_experiment._get_penetration_depth_and_correlograms()

        self.assertEqual([1, 2], list(penetration_roi.keys()))
        self.assertEqual([1, 2], list(mu_roi.keys()))

        for test_unique in list(penetration_roi.values()) + list(mu_roi.values()):
            self.assertAlmostEqual(test_unique[0], test_unique[3], places=12)
            self.assertAlmostEqual(test_unique[0], test_unique[4], places=12)
            self.assertAlmostEqual(test_unique[1], test_unique[2], places=12)
            self.assertNotEqual(test_unique[0], test_unique[1])

    def test_generate_simulation_images(self):
        self.sim_experiment.generate_simulation_images()

        # check open values
        self.assertEqual(np.max(self.sim_experiment.H0[:3, :2, :]), 1)
        self.assertEqual(np.min(self.sim_experiment.H0[:3, :2, :]), 1)

        self.assertEqual(np.max(self.sim_experiment.H1byH0[:3, :2, :]), 1)
        self.assertEqual(np.min(self.sim_experiment.H1byH0[:3, :2, :]), 1)

        # check ROI 2 values
        self.assertEqual(list(np.max(self.sim_experiment.H0[:2, 2:, :], axis=(0, 1))),
                         list(self.sim_experiment.H0[0, 2, :]))
        self.assertEqual(list(np.min(self.sim_experiment.H0[:2, 2:, :], axis=(0, 1))),
                         list(self.sim_experiment.H0[0, 2, :]))

        self.assertEqual(list(np.max(self.sim_experiment.H1byH0[:2, 2:, :], axis=(0, 1))),
                         list(self.sim_experiment.H1byH0[0, 2, :]))
        self.assertEqual(list(np.min(self.sim_experiment.H1byH0[:2, 2:, :], axis=(0, 1))),
                         list(self.sim_experiment.H1byH0[0, 2, :]))

        # check ROI 3 values
        self.assertEqual(list(np.max(self.sim_experiment.H0[2:, 2:, :], axis=(0, 1))),
                         list(self.sim_experiment.H0[2, 2, :]))
        self.assertEqual(list(np.min(self.sim_experiment.H0[2:, 2:, :], axis=(0, 1))),
                         list(self.sim_experiment.H0[2, 2, :]))

        self.assertEqual(list(np.max(self.sim_experiment.H0[3:, :2, :], axis=(0, 1))),
                         list(self.sim_experiment.H0[3, 0, :]))
        self.assertEqual(list(np.min(self.sim_experiment.H0[3:, :2, :], axis=(0, 1))),
                         list(self.sim_experiment.H0[3, 0, :]))

        self.assertEqual(list(np.max(self.sim_experiment.H1byH0[2:, 2:, :], axis=(0, 1))),
                         list(self.sim_experiment.H1byH0[2, 2, :]))
        self.assertEqual(list(np.min(self.sim_experiment.H1byH0[2:, 2:, :], axis=(0, 1))),
                         list(self.sim_experiment.H1byH0[2, 2, :]))

        self.assertEqual(list(np.max(self.sim_experiment.H1byH0[3:, :2, :], axis=(0, 1))),
                         list(self.sim_experiment.H1byH0[3, 0, :]))
        self.assertEqual(list(np.min(self.sim_experiment.H1byH0[3:, :2, :], axis=(0, 1))),
                         list(self.sim_experiment.H1byH0[3, 0, :]))

        self.assertNotEqual(list(self.sim_experiment.H0[2, 2, :]),
                            list(self.sim_experiment.H0[3, 0, :]))

        self.assertNotEqual(list(self.sim_experiment.H1byH0[2, 2, :]),
                            list(self.sim_experiment.H1byH0[3, 0, :]))


if __name__ == "__main__":
    unittest.main()
