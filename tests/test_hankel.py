import numpy as np
import unittest

import sasmodels.core
import sasmodels.bumps_model

from correlogram_tools import hankel


def df_strobl(xi, radius, phi, sld, sld_solvent, wavelength, thickness):
    """
    Calculates the dark field intensity for system of spheres using the functional form in:

    "General solution for quantitative dark-field contrast imaging with grading interferometers"
    M. Strobl
    Scientific Reports, 4:7243, 2014
    DOI: 10.1038/srep07243

    Parameters:
    -----------
    xi: autocorrelation lengths, Angstroms, must be greater than 0
    radius: sphere radius, Angstroms
    phi: volume fraction
    sld: scattering length density of spheres, 1e-6 Ang^-2
    sld_solvent: scattering length density of spheres, 1e-6 Ang^-2
    wavelength: neutron wavelength, Angstroms
    thickness: pathlength, cm

    """
    xi_trim = xi[np.where((xi <= radius * 2) & (xi > 0))]
    xi_r = xi_trim / radius
    G = np.sqrt(1 - (xi_r / 2) ** 2) * (1 + (1 / 8) * xi_r ** 2) + (1 / 2) * (xi_r ** 2) * (
            1 - (xi_r / 4) ** 2) * np.log(xi_r / (2 + np.sqrt(4 - xi_r ** 2)))

    contrast = 1e-12 * (sld - sld_solvent) ** 2
    Sigma = (3 / 2) * phi * contrast * wavelength ** 2 * radius * 1e8  # unit changed to 1/cm to cancel with thickness

    DF = np.exp(Sigma * thickness * (G - 1))

    return xi_trim, DF


class TestHankel(unittest.TestCase):

    def test_sim_darkfield(self):
        sld = 1
        sld_solvent = 4
        radius = 1000
        phi = 0.05
        wavelength = 4
        thickness = 0.2
        xi = np.arange(10, 10000, 10)

        # sasmodels model setup
        kernel = sasmodels.core.load_model("sphere")
        params = {
            "radius": radius,
            "sld": sld,
            "sld_solvent": sld_solvent,
            "background": 0,
            "scale": phi,
        }
        model = sasmodels.bumps_model.Model(kernel, **params)

        # reference dark field intensity from analytical model for spheres
        xi_strobl, DF_strobl = df_strobl(xi, radius, phi, sld, sld_solvent, wavelength, thickness)

        # dark field intensity calculated in hankel script in correlogram-tools
        DF_hankel = hankel.sim_visibility(xi, model, wavelength, thickness)
        trim_filter = np.where((xi <= radius * 2) & (xi > 0))
        DF_hankel = DF_hankel.reshape(-1)[trim_filter]

        self.assertListEqual(list(xi_strobl), list(xi[trim_filter]))

        # calculating error
        percent_error = (DF_hankel - DF_strobl) * 100 / DF_strobl
        self.assertLessEqual(max(percent_error), 0.01)


if __name__ == "__main__":
    unittest.main()
