import os
from pathlib import Path
import unittest

import numpy as np

from correlogram_tools import sim_measurements
from correlogram_tools.sim_measurements import SimMeasurements, gen_measurements


class TestSimMeasurements(unittest.TestCase):

    def setUp(self):
        self.test_config = {
            "measurements": [
                {
                    "measurement_mode": "multi-scan",
                    "xi": {
                        "mode": "calculated"
                    },
                    "moire": {
                        "mode": "discrete",
                        "value": [0.4, 0.7, 1, 2],
                        "units": "mm"
                    },
                    "z": {
                        "mode": "range",
                        "value": [30, 600, 20, "linear"],
                        "units": "mm"
                    },
                    "wavelength": {
                        "mode": "fixed",
                        "value": [3],
                        "units": "Ang"
                    }
                }]
        }
        self.config_path = Path(__file__).absolute().parent / "test_data/test_config.json"
        self.sim_measurements = SimMeasurements(config_dict=self.test_config, config_path=self.config_path)

    def test_check_units(self):
        accepted_xi_units = sim_measurements.accepted_units["xi"]
        sim_measurements.check_units("xi", accepted_xi_units)
        self.assertRaises(Exception, sim_measurements.check_units, "xi", "not_units")

    def test_range_interpreter_log(self):
        """check that the log range works"""
        log_answer = [1e1, 1e2, 1e3, 1e4, 1e5]
        log_check = list(sim_measurements.range_interpreter([1e1, 1e5, 5, "log"]))
        self.assertEqual(log_answer, log_check)

    def test_range_interpreter_linear(self):
        """check that the linear range works"""
        linear_answer = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        linear_check = list(sim_measurements.range_interpreter([1, 10, 10, "linear"]))
        self.assertEqual(linear_answer, linear_check)

    def test_range_interpreter_type(self):
        """check that an exception is raised for wrong types in value"""
        type_check = ["", 10, 10, "linear"]
        self.assertRaises(Exception, sim_measurements.range_interpreter, type_check)
        type_check = [1, "", 10, "linear"]
        self.assertRaises(Exception, sim_measurements.range_interpreter, type_check)
        type_check = [1, 10, "", "linear"]
        self.assertRaises(Exception, sim_measurements.range_interpreter, type_check)

    def test_range_interpreter_keyword(self):
        """check that only valid keywords can be used for range type"""
        keyword_check = [1, 10, 10, "not_linear"]
        self.assertRaises(Exception, sim_measurements.range_interpreter, keyword_check)

    def test_check_lengths(self):
        self.assertRaises(Exception, sim_measurements.check_lengths, [np.array([1, 2, 3]), [1, 2, 3], [3, 4]])
        sim_measurements.check_lengths([np.array([1, 2, 3]), [4, 5, 6], [None], [1]])

    def test_get_missing_variable_lengths(self):
        """check that the lengths of the provided arrays are handled correctly"""
        self.assertRaises(Exception, sim_measurements.get_missing_variable,
                          xi=[1]*5, moire=[2]*2, wavelength=[1], z=[4]*3)
        sim_measurements.get_missing_variable("wavelength", xi=[1] * 3, moire=[2] * 3, wavelength=[3], z=[4, 5, 6])

    def test_get_missing_variable_xi(self):
        """test retrieve xi"""
        xi = np.array([75, 150, 225])  # nm
        z = np.array([500, 1000, 1500])  # mm
        wavelength = [0.3]  # nm
        moire = [2]  # mm
        self.assertEqual(
            list(xi), list(sim_measurements.get_missing_variable("xi", moire=moire, wavelength=wavelength, z=z)))

    def test_get_missing_variable_extra_args(self):
        """test that the function still returns the variable with extra arguments"""
        xi = np.array([75, 150, 225])  # nm
        z = np.array([500, 1000, 1500])  # mm
        wavelength = [0.3]  # nm
        moire = [2]  # mm
        self.assertEqual(
            list(xi), list(sim_measurements.get_missing_variable("xi", xi=xi, moire=moire, wavelength=wavelength, z=z)))
        self.assertRaises(
            Exception, sim_measurements.get_missing_variable, "xi", wavelength=wavelength, z=z
        )

    def test_get_missing_variable_moire(self):
        """test retrieve moire"""
        xi = np.array([75, 150, 225])  # nm
        z = np.array([500, 1000, 1500])  # mm
        wavelength = [0.3]  # nm
        moire = [2]  # mm
        self.assertEqual(
            list(moire)*3, list(sim_measurements.get_missing_variable("moire", xi=xi, wavelength=wavelength, z=z)))
        self.assertRaises(
            Exception, sim_measurements.get_missing_variable, "moire", xi=xi, z=z, moire=moire
        )

    def test_get_missing_variable_wavelength(self):
        """test retrieve wavelength"""
        xi = np.array([75, 150, 225])  # nm
        z = np.array([500, 1000, 1500])  # mm
        wavelength = [0.3]  # nm
        moire = [2]  # mm
        self.assertEqual(
            list(wavelength)*3, list(sim_measurements.get_missing_variable("wavelength", moire=moire, xi=xi, z=z)))
        self.assertRaises(
            Exception, sim_measurements.get_missing_variable, "wavelength", moire=moire, xi=xi
        )

    def test_get_missing_variable_z(self):
        """test retrieve z"""
        xi = np.array([75, 150, 225])  # nm
        z = np.array([500, 1000, 1500])  # mm
        wavelength = [0.3]  # nm
        moire = [2]  # mm
        self.assertEqual(
            list(z), list(sim_measurements.get_missing_variable("z", moire=moire, wavelength=wavelength, xi=xi)))
        self.assertRaises(
            Exception, sim_measurements.get_missing_variable, "z", moire=moire, wavelength=wavelength
        )

    def test_get_variable_details(self):
        test_dict = {
            "mode": "range",
            "value": [10, 100, 10, "linear"],
            "units": "nm",
        }
        mode, value, units = sim_measurements.get_variable_details("xi", test_dict)
        self.assertEqual(mode, "range")
        self.assertEqual(value, [10, 100, 10, "linear"])
        self.assertEqual(units, "nm")

    def test_get_variable_details_missing_units(self):
        test_dict = {
            "mode": "range",
            "value": [10, 100, 10, "linear"],
        }
        mode, value, units = sim_measurements.get_variable_details("xi", test_dict)
        self.assertEqual(mode, "range")
        self.assertEqual(value, [10, 100, 10, "linear"])
        self.assertEqual(units, sim_measurements.accepted_units["xi"])

    def test_get_variable_details_wrong_units(self):
        test_dict = {
            "mode": "range",
            "value": [10, 100, 10, "linear"],
            "units": "mm",
        }
        self.assertRaises(Exception,
                          sim_measurements.get_variable_details,
                          "xi",
                          test_dict)

    def test_get_variable_details_missing_mode(self):
        test_dict = {
            "value": [10, 100, 10, "linear"],
            "units": "mm",
        }
        self.assertRaises(Exception,
                          sim_measurements.get_variable_details,
                          "xi",
                          test_dict)

    def test_get_variable_info_missing_value(self):
        test_dict = {
            "mode": "range",
            "units": "mm",
        }
        self.assertRaises(Exception,
                          sim_measurements.get_variable_details,
                          "xi",
                          test_dict)

    def test_xi_scan_xi_mode_range(self):
        test_measurement = {
            "xi": {"mode": "range", "value": [10, 110, 5, "linear"]},
            "wavelength": {"mode": "fixed", "value": [4]},
            "moire": {"mode": "fixed", "value": [1]},
            "z": {"mode": "continuous", "value": [10, 600]}
        }

        xi, moire, wavelength, z = sim_measurements.gen_xi_scan(test_measurement)
        self.assertListEqual(list(xi), [10., 35., 60., 85., 110.])
        self.assertListEqual(list(moire), [1., 1., 1., 1., 1.])
        self.assertListEqual(list(wavelength), [0.4, 0.4, 0.4, 0.4, 0.4])
        self.assertListEqual(list(z), [25., 87.5, 150., 212.5, 275.])

    def test_xi_scan_xi_mode_discrete(self):
        test_measurement = {
            "xi": {"mode": "discrete", "value": [10, 35, 60, 85, 110]},
            "wavelength": {"mode": "fixed", "value": [4]},
            "moire": {"mode": "fixed", "value": [1]},
            "z": {"mode": "continuous", "value": [10, 600]}
        }

        xi, moire, wavelength, z = sim_measurements.gen_xi_scan(test_measurement)
        self.assertListEqual(list(xi), [10., 35., 60., 85., 110.])
        self.assertListEqual(list(moire), [1., 1., 1., 1., 1.])
        self.assertListEqual(list(wavelength), [0.4, 0.4, 0.4, 0.4, 0.4])
        self.assertListEqual(list(z), [25., 87.5, 150., 212.5, 275.])

    def test_xi_scan_xi_mode_fixed(self):
        test_measurement = {
            "xi": {"mode": "fixed", "value": [10]},
        }

        self.assertRaises(ValueError, sim_measurements.gen_xi_scan, test_measurement)

    def test_xi_scan_xi_mode_continuous(self):
        test_measurement = {
            "xi": {"mode": "continuous", "value": [10, 100]},
        }

        self.assertRaises(ValueError, sim_measurements.gen_xi_scan, test_measurement)

    def test_xi_scan_xi_mode_calculated(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
        }

        self.assertRaises(ValueError, sim_measurements.gen_xi_scan, test_measurement)

    def test_xi_scan_xi_mode_file(self):
        test_measurement = {
            "xi": {"mode": "file", "value": "filepath.txt"},
        }

        self.assertRaises(ValueError, sim_measurements.gen_xi_scan, test_measurement)

    def test_xi_scan_wavelength_mode_range(self):
        test_measurement = {
            "xi": {"mode": "discrete", "value": [10, 35, 60, 85, 110]},
            "wavelength": {"mode": "range", "value": [4, 10, 6, "linear"]},
            "moire": {"mode": "fixed", "value": [1]},
            "z": {"mode": "continuous", "value": [10, 600]}
        }

        self.assertRaises(ValueError, sim_measurements.gen_xi_scan, test_measurement)

    def test_xi_scan_wavelength_mode_discrete(self):
        test_measurement = {
            "xi": {"mode": "discrete", "value": [10, 35, 60, 85, 110]},
            "wavelength": {"mode": "discrete", "value": [4, 5, 6]},
            "moire": {"mode": "fixed", "value": [1]},
            "z": {"mode": "continuous", "value": [10, 600]}
        }

        self.assertRaises(ValueError, sim_measurements.gen_xi_scan, test_measurement)

    def test_xi_scan_wavelength_mode_continuous(self):
        test_measurement = {
            "xi": {"mode": "discrete", "value": [10, 35, 60, 85, 110]},
            "wavelength": {"mode": "continuous", "value": [4, 10]},
            "moire": {"mode": "fixed", "value": [1]},
            "z": {"mode": "continuous", "value": [10, 600]}
        }

        self.assertRaises(ValueError, sim_measurements.gen_xi_scan, test_measurement)

    def test_xi_scan_wavelength_mode_calculated(self):
        test_measurement = {
            "xi": {"mode": "discrete", "value": [10, 35, 60, 85, 110]},
            "wavelength": {"mode": "calculated"},
            "moire": {"mode": "fixed", "value": [1]},
            "z": {"mode": "continuous", "value": [10, 600]}
        }

        self.assertRaises(ValueError, sim_measurements.gen_xi_scan, test_measurement)

    def test_xi_scan_wavelength_mode_file(self):
        test_measurement = {
            "xi": {"mode": "discrete", "value": [10, 35, 60, 85, 110]},
            "wavelength": {"mode": "file", "value": "filepath.txt"},
            "moire": {"mode": "fixed", "value": [1]},
            "z": {"mode": "continuous", "value": [10, 600]}
        }

        self.assertRaises(ValueError, sim_measurements.gen_xi_scan, test_measurement)

    def test_xi_scan_moire_discrete_z_continuous(self):
        test_measurement = {
            "xi": {"mode": "discrete", "value": [10, 35, 60, 85, 110]},
            "wavelength": {"mode": "fixed", "value": [4]},
            "moire": {"mode": "discrete", "value": [1, 2]},
            "z": {"mode": "continuous", "value": [30, 325]}
        }

        xi, moire, wavelength, z = sim_measurements.gen_xi_scan(test_measurement)
        self.assertListEqual(list(xi), [10., 35., 60., 85., 110.])
        self.assertListEqual(list(moire), [2., 2., 2., 1., 1.])  # will maximize P when possible
        self.assertListEqual(list(wavelength), [0.4, 0.4, 0.4, 0.4, 0.4])
        self.assertListEqual(list(z), [50., 175., 300., 212.5, 275.])

    def test_xi_scan_z_limits(self):
        test_measurement = {
            "xi": {"mode": "discrete", "value": [10, 35, 60, 85, 110]},
            "wavelength": {"mode": "fixed", "value": [4]},
            "moire": {"mode": "discrete", "value": [1, 2]},
            "z": {"mode": "continuous", "value": [90, 260]}
        }

        xi, moire, wavelength, z = sim_measurements.gen_xi_scan(test_measurement)
        self.assertListEqual(list(xi), [35., 60., 85.])
        self.assertListEqual(list(moire), [2., 1., 1.])  # will maximize P when possible
        self.assertListEqual(list(wavelength), [0.4, 0.4, 0.4])
        self.assertListEqual(list(z), [175., 150., 212.5])  # filtered based on z range!

    def test_xi_scan_moire_continuous_z_fixed(self):
        test_measurement = {
            "xi": {"mode": "discrete", "value": [10, 35, 60, 85, 110]},
            "wavelength": {"mode": "fixed", "value": [4]},
            "moire": {"mode": "continuous", "value": [0.2, 2]},
            "z": {"mode": "fixed", "value": [100]}
        }

        xi, moire, wavelength, z = sim_measurements.gen_xi_scan(test_measurement)
        self.assertListEqual(list(xi), [35.0, 60.0, 85.0, 110.0])
        self.assertListEqual(list(np.round(moire, 2)), [1.14, 0.67, 0.47, 0.36])  # will maximize P when possible
        self.assertListEqual(list(wavelength), [0.4, 0.4, 0.4, 0.4])
        self.assertListEqual(list(z), [100., 100., 100., 100.])

    def test_xi_scan_moire_continuous_z_discrete(self):
        test_measurement = {
            "xi": {"mode": "discrete", "value": [10, 35, 60, 85, 110]},
            "wavelength": {"mode": "fixed", "value": [4]},
            "moire": {"mode": "continuous", "value": [0.2, 2]},
            "z": {"mode": "fixed", "value": [50, 100]}
        }

        xi, moire, wavelength, z = sim_measurements.gen_xi_scan(test_measurement)
        self.assertListEqual(list(xi), [10.0, 35.0, 60.0, 85.0, 110.0])
        self.assertListEqual(list(np.round(moire, 2)), [2., 1.14, 0.67, 0.47, 0.36])  # will maximize P when possible
        self.assertListEqual(list(wavelength), [0.4, 0.4, 0.4, 0.4, 0.4])
        self.assertListEqual(list(z), [50., 100., 100., 100., 100.])

    def test_xi_scan_moire_continuous_z_continuous(self):
        test_measurement = {
            "xi": {"mode": "discrete", "value": [10, 35, 60, 85, 110]},
            "wavelength": {"mode": "fixed", "value": [4]},
            "moire": {"mode": "continuous", "value": [0.2, 2]},
            "z": {"mode": "continuous", "value": [50, 100]}
        }

        self.assertRaises(ValueError, sim_measurements.gen_xi_scan, test_measurement)

    def test_wavelength_scan_wavelength_range(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "range", "value": [2, 4, 5, "linear"]},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "fixed", "value": [50]}
        }
        xi, moire, wavelength, z = sim_measurements.gen_wavelength_scan(test_measurement)
        self.assertListEqual(list(xi), [5., 6.25, 7.5, 8.75, 10.])
        self.assertListEqual(list(moire), [2., 2., 2., 2., 2.])
        self.assertListEqual(list(wavelength), [0.2, 0.25, 0.3, 0.35, 0.4])
        self.assertListEqual(list(z), [50., 50., 50., 50., 50.])

    def test_wavelength_scan_wavelength_discrete(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "discrete", "value": [2, 2.5, 3, 3.5, 4]},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "fixed", "value": [50]}
        }
        xi, moire, wavelength, z = sim_measurements.gen_wavelength_scan(test_measurement)
        self.assertListEqual(list(xi), [5., 6.25, 7.5, 8.75, 10.])
        self.assertListEqual(list(moire), [2., 2., 2., 2., 2.])
        self.assertListEqual(list(wavelength), [0.2, 0.25, 0.3, 0.35, 0.4])
        self.assertListEqual(list(z), [50., 50., 50., 50., 50.])

    def test_wavelength_scan_wavelength_check(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "not_a_mode", "value": [2, 4, 5, "linear"]},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "fixed", "value": [50]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_wavelength_scan, test_measurement)

    def test_wavelength_scan_xi_check(self):
        test_measurement = {
            "xi": {"mode": "discrete", "value": [2]},
            "wavelength": {"mode": "range", "value": [2, 4, 5, "linear"]},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "fixed", "value": [50]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_wavelength_scan, test_measurement)

    def test_wavelength_scan_moire_check(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "range", "value": [2, 4, 5, "linear"]},
            "moire": {"mode": "discrete", "value": [2]},
            "z": {"mode": "fixed", "value": [50]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_wavelength_scan, test_measurement)

    def test_wavelength_scan_z_check(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "range", "value": [2, 4, 5, "linear"]},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "discrete", "value": [50]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_wavelength_scan, test_measurement)

    def test_z_scan_z_range(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "fixed", "value": [4]},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "range", "value": [50, 100, 3, "linear"]}
        }
        xi, moire, wavelength, z = sim_measurements.gen_z_scan(test_measurement)
        self.assertListEqual(list(xi), [10., 15., 20.])
        self.assertListEqual(list(moire), [2., 2., 2.])
        self.assertListEqual(list(wavelength), [0.4, 0.4, 0.4])
        self.assertListEqual(list(z), [50., 75., 100.])

    def test_z_scan_z_discrete(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "fixed", "value": [4]},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "discrete", "value": [50, 75, 100]}
        }
        xi, moire, wavelength, z = sim_measurements.gen_z_scan(test_measurement)
        self.assertListEqual(list(xi), [10., 15., 20.])
        self.assertListEqual(list(moire), [2., 2., 2.])
        self.assertListEqual(list(wavelength), [0.4, 0.4, 0.4])
        self.assertListEqual(list(z), [50., 75., 100.])

    def test_z_scan_z_check(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "fixed", "value": [4]},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "fixed", "value": [50]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_z_scan, test_measurement)

    def test_z_scan_xi_check(self):
        test_measurement = {
            "xi": {"mode": "range", "value": [1, 3, 3, "linear"]},
            "wavelength": {"mode": "fixed", "value": [4]},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "discrete", "value": [50, 75, 100]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_z_scan, test_measurement)

    def test_z_scan_moire_check(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "fixed", "value": [4]},
            "moire": {"mode": "discrete", "value": [2]},
            "z": {"mode": "discrete", "value": [50, 75, 100]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_z_scan, test_measurement)

    def test_z_scan_wavelength_check(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "discrete", "value": [4]},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "discrete", "value": [50, 75, 100]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_z_scan, test_measurement)

    def test_moire_scan_moire_range(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "fixed", "value": [3]},
            "moire": {"mode": "range", "value": [1, 2, 3, "linear"]},
            "z": {"mode": "fixed", "value": [50]}
        }
        xi, moire, wavelength, z = sim_measurements.gen_moire_scan(test_measurement)
        self.assertListEqual(list(xi), [15., 10., 7.5])
        self.assertListEqual(list(moire), [1., 1.5, 2.])
        self.assertListEqual(list(wavelength), [0.3, 0.3, 0.3])
        self.assertListEqual(list(z), [50., 50., 50.])

    def test_moire_scan_moire_discrete(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "fixed", "value": [3]},
            "moire": {"mode": "discrete", "value": [1, 1.5, 2]},
            "z": {"mode": "fixed", "value": [50]}
        }
        xi, moire, wavelength, z = sim_measurements.gen_moire_scan(test_measurement)
        self.assertListEqual(list(xi), [15., 10., 7.5])
        self.assertListEqual(list(moire), [1., 1.5, 2.])
        self.assertListEqual(list(wavelength), [0.3, 0.3, 0.3])
        self.assertListEqual(list(z), [50., 50., 50.])

    def test_moire_scan_moire_check(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "fixed", "value": [3]},
            "moire": {"mode": "continuous", "value": [1, 1.5]},
            "z": {"mode": "fixed", "value": [50]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_moire_scan, test_measurement)

    def test_moire_scan_xi_check(self):
        test_measurement = {
            "xi": {"mode": "range", "value": [1, 2, 3, "linear"]},
            "wavelength": {"mode": "fixed", "value": [3]},
            "moire": {"mode": "discrete", "value": [1, 1.5, 2]},
            "z": {"mode": "fixed", "value": [50]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_moire_scan, test_measurement)

    def test_moire_scan_z_check(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "fixed", "value": [3]},
            "moire": {"mode": "discrete", "value": [1, 1.5, 2]},
            "z": {"mode": "discrete", "value": [50]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_moire_scan, test_measurement)

    def test_moire_scan_wavelength_check(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "discrete", "value": [3]},
            "moire": {"mode": "discrete", "value": [1, 1.5, 2]},
            "z": {"mode": "fixed", "value": [50]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_moire_scan, test_measurement)

    def test_gen_multi_scan(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "discrete", "value": [2, 3, 4]},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "range", "value": [50, 100, 3, "linear"]}
        }
        xi, moire, wavelength, z = sim_measurements.gen_multi_scan(test_measurement)
        self.assertListEqual(list(xi), [5., 7.5, 10., 7.5, 11.25, 15., 10., 15., 20.])
        self.assertListEqual(list(moire), [2., 2., 2., 2., 2., 2., 2., 2., 2.])
        self.assertListEqual(list(wavelength), [0.2, 0.2, 0.2, 0.3, 0.3, 0.3, 0.4, 0.4, 0.4])
        self.assertListEqual(list(z), [50., 75., 100., 50., 75., 100., 50., 75., 100.])

    def test_gen_multi_scan_xi_mode(self):
        test_measurement = {
            "xi": {"mode": "fixed", "value": [100]},
            "wavelength": {"mode": "discrete", "value": [2, 3, 4]},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "range", "value": [50, 100, 3, "linear"]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_multi_scan, test_measurement)

    def test_gen_multi_scan_wavelength_mode(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "calculated"},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "range", "value": [50, 100, 3, "linear"]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_multi_scan, test_measurement)

    def test_gen_multi_scan_moire_mode(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "discrete", "value": [2, 3, 4]},
            "moire": {"mode": "calculated", "value": [2]},
            "z": {"mode": "range", "value": [50, 100, 3, "linear"]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_multi_scan, test_measurement)

    def test_gen_multi_scan_z_mode(self):
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "discrete", "value": [2, 3, 4]},
            "moire": {"mode": "fixed", "value": [2]},
            "z": {"mode": "calculated", "value": [50, 100, 3, "linear"]}
        }
        self.assertRaises(ValueError, sim_measurements.gen_multi_scan, test_measurement)

    def test_gen_custom_scan(self):
        config_path = self.config_path
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "file", "value": "./wavelength.txt"},
            "moire": {"mode": "file", "value": "./moire.txt"},
            "z": {"mode": "file", "value": "./z.txt"}
        }
        xi, moire, wavelength, z = sim_measurements.gen_custom_scan(test_measurement, config_path)
        self.assertListEqual(list(xi), [5., 11.25, 20.])
        self.assertListEqual(list(moire), [2., 2., 2.])
        self.assertListEqual(list(wavelength), [0.2, 0.3, 0.4])
        self.assertListEqual(list(z), [50., 75., 100.])

    def test_gen_custom_scan_length_check(self):
        config_path = self.config_path
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "file", "value": "./wavelength.txt"},
            "moire": {"mode": "file", "value": "./moire_length_check.txt"},
            "z": {"mode": "file", "value": "./z.txt"}
        }
        self.assertRaises(Exception, sim_measurements.gen_custom_scan, test_measurement, config_path)

    def test_gen_custom_scan_xi_mode(self):
        config_path = self.config_path
        test_measurement = {
            "xi": {"mode": "fixed", "value": [100]},
            "wavelength": {"mode": "file", "value": "./wavelength.txt"},
            "moire": {"mode": "file", "value": "./moire.txt"},
            "z": {"mode": "file", "value": "./z.txt"}
        }
        self.assertRaises(ValueError, sim_measurements.gen_custom_scan, test_measurement, config_path)

    def test_gen_custom_scan_wavelength_mode(self):
        config_path = self.config_path
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "calculated", "value": "./wavelength.txt"},
            "moire": {"mode": "file", "value": "./moire.txt"},
            "z": {"mode": "file", "value": "./z.txt"}
        }
        self.assertRaises(ValueError, sim_measurements.gen_custom_scan, test_measurement, config_path)

    def test_gen_custom_scan_moire_mode(self):
        config_path = self.config_path
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "file", "value": "./wavelength.txt"},
            "moire": {"mode": "calculated", "value": "./moire.txt"},
            "z": {"mode": "file", "value": "./z.txt"}
        }
        self.assertRaises(ValueError, sim_measurements.gen_custom_scan, test_measurement, config_path)

    def test_gen_custom_scan_z_mode(self):
        config_path = self.config_path
        test_measurement = {
            "xi": {"mode": "calculated"},
            "wavelength": {"mode": "file", "value": "./wavelength.txt"},
            "moire": {"mode": "file", "value": "./moire.txt"},
            "z": {"mode": "calculated", "value": "./z.txt"}
        }
        self.assertRaises(ValueError, sim_measurements.gen_custom_scan, test_measurement, config_path)

    def test_create_measurements(self):
        test_config = {
            "measurements": [{
                "measurement_mode": "multi-scan",
                "xi": {"mode": "calculated"},
                "wavelength": {"mode": "discrete", "value": [2, 3, 4]},
                "moire": {"mode": "fixed", "value": [2]},
                "z": {"mode": "range", "value": [50, 100, 3, "linear"]},
            }, {
                "measurement_mode": "wavelength-scan",
                "xi": {"mode": "calculated"},
                "wavelength": {"mode": "discrete", "value": [2, 2.5, 3, 3.5, 4]},
                "moire": {"mode": "fixed", "value": [2]},
                "z": {"mode": "fixed", "value": [50]}
            }]
        }
        sim = SimMeasurements(config_path="here.json", config_dict=test_config)
        xi = sim.measurements_xi
        moire = sim.measurements_moire
        wavelength = sim.measurements_wavelength
        z = sim.measurements_z

        self.assertListEqual(list(xi), [5., 5., 6.25, 7.5, 7.5, 7.5, 8.75, 10, 10, 10, 11.25, 15, 15, 20])
        self.assertListEqual(list(moire), [2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2., 2.])
        self.assertListEqual(list(wavelength), [0.2, 0.2, 0.25, 0.2, 0.3, 0.3, 0.35, 0.2, 0.4, 0.4, 0.3, 0.3, 0.4, 0.4])
        self.assertListEqual(list(z), [50, 50, 50, 75, 50, 50, 50, 100, 50, 50, 75, 100, 75, 100])

    def test_create_measurements_missing_measurement_mode(self):
        test_config = {
            "measurements": [{
                "xi": {"mode": "calculated"},
                "wavelength": {"mode": "discrete", "value": [2, 3, 4]},
                "moire": {"mode": "fixed", "value": [2]},
                "z": {"mode": "range", "value": [50, 100, 3, "linear"]},
            }, {
                "measurement_mode": "wavelength-scan",
                "xi": {"mode": "calculated"},
                "wavelength": {"mode": "discrete", "value": [2, 2.5, 3, 3.5, 4]},
                "moire": {"mode": "fixed", "value": [2]},
                "z": {"mode": "fixed", "value": [50]}
            }]
        }
        self.assertRaises(KeyError, SimMeasurements, config_path="here.json", config_dict=test_config)

    def test_create_measurements_measurement_mode(self):
        test_config = {
            "measurements": [{
                "measurement_mode": "not-a-mode",
                "xi": {"mode": "calculated"},
                "wavelength": {"mode": "discrete", "value": [2, 3, 4]},
                "moire": {"mode": "fixed", "value": [2]},
                "z": {"mode": "range", "value": [50, 100, 3, "linear"]},
            }, {
                "measurement_mode": "wavelength-scan",
                "xi": {"mode": "calculated"},
                "wavelength": {"mode": "discrete", "value": [2, 2.5, 3, 3.5, 4]},
                "moire": {"mode": "fixed", "value": [2]},
                "z": {"mode": "fixed", "value": [50]}
            }]
        }
        self.assertRaises(ValueError, SimMeasurements, config_path="here.json", config_dict=test_config)

    def test_create_measurements_missing_xi(self):
        test_config = {
            "measurements": [{
                "measurement-mode": "multi-scan",
                "wavelength": {"mode": "discrete", "value": [2, 3, 4]},
                "moire": {"mode": "fixed", "value": [2]},
                "z": {"mode": "range", "value": [50, 100, 3, "linear"]},
            }, {
                "measurement-mode": "wavelength-scan",
                "xi": {"mode": "calculated"},
                "wavelength": {"mode": "discrete", "value": [2, 2.5, 3, 3.5, 4]},
                "moire": {"mode": "fixed", "value": [2]},
                "z": {"mode": "fixed", "value": [50]}
            }]
        }
        self.assertRaises(KeyError, SimMeasurements, config_path="here.json", config_dict=test_config)

    def test_create_measurements_missing_wavelength(self):
        test_config = {
            "measurements": [{
                "measurement-mode": "multi-scan",
                "xi": {"mode": "calculated"},
                "moire": {"mode": "fixed", "value": [2]},
                "z": {"mode": "range", "value": [50, 100, 3, "linear"]},
            }, {
                "measurement-mode": "wavelength-scan",
                "xi": {"mode": "calculated"},
                "wavelength": {"mode": "discrete", "value": [2, 2.5, 3, 3.5, 4]},
                "moire": {"mode": "fixed", "value": [2]},
                "z": {"mode": "fixed", "value": [50]}
            }]
        }
        self.assertRaises(KeyError, SimMeasurements, config_path="here.json", config_dict=test_config)

    def test_create_measurements_missing_moire(self):
        test_config = {
            "measurements": [{
                "measurement-mode": "multi-scan",
                "xi": {"mode": "calculated"},
                "wavelength": {"mode": "discrete", "value": [2, 3, 4]},
                "z": {"mode": "range", "value": [50, 100, 3, "linear"]},
            }, {
                "measurement-mode": "wavelength-scan",
                "xi": {"mode": "calculated"},
                "wavelength": {"mode": "discrete", "value": [2, 2.5, 3, 3.5, 4]},
                "moire": {"mode": "fixed", "value": [2]},
                "z": {"mode": "fixed", "value": [50]}
            }]
        }
        self.assertRaises(KeyError, SimMeasurements, config_path="here.json", config_dict=test_config)

    def test_create_measurements_missing_z(self):
        test_config = {
            "measurements": [{
                "measurement-mode": "multi-scan",
                "xi": {"mode": "calculated"},
                "wavelength": {"mode": "discrete", "value": [2, 3, 4]},
                "moire": {"mode": "fixed", "value": [2]},
            }, {
                "measurement-mode": "wavelength-scan",
                "xi": {"mode": "calculated"},
                "wavelength": {"mode": "discrete", "value": [2, 2.5, 3, 3.5, 4]},
                "moire": {"mode": "fixed", "value": [2]},
                "z": {"mode": "fixed", "value": [50]}
            }]
        }
        self.assertRaises(KeyError, SimMeasurements, config_path="here.json", config_dict=test_config)


if __name__ == "__main__":
    unittest.main()
