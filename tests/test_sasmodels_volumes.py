import unittest

import numpy as np

from correlogram_tools.sasmodels_volumes import get_volume_fractions, HOMOGENEOUS_SHAPES


def sphere_volume(radius):
    return (4/3)*np.pi*radius**3


def cylinder_volume(radius, length):
    return np.pi*radius**2*length


def ellipsoid_volume(radius_polar, radius_equatorial):
    return (4/3)*np.pi*radius_polar*radius_equatorial**2


class TestSasmodelsVolumes(unittest.TestCase):

    def test_homogeneous_prefix(self):
        """Checks that the correct scale is used when multiple model components with prefixes are implemented."""
        params = {
            "A_scale": [0.05],
            "B_scale": [0.07],
        }

        for model in HOMOGENEOUS_SHAPES:
            self.assertListEqual(params["A_scale"], get_volume_fractions(model, "A_", "sld", params))
            self.assertListEqual(params["B_scale"], get_volume_fractions(model, "B_", "sld", params))
            self.assertListEqual(
                list(1-np.array(params["A_scale"])),
                get_volume_fractions(model, "A_", "sld_solvent", params)
            )
            self.assertListEqual(
                list(1-np.array(params["B_scale"])),
                get_volume_fractions(model, "B_", "sld_solvent", params)
            )

    def test_homogeneous_list(self):
        """Checks that scales set as a list of parameters (multiple ROIs) are applied to the sld components."""
        params = {
            "scale": [0.05, 0.07, 0.1],
        }

        for model in HOMOGENEOUS_SHAPES:
            self.assertListEqual(params["scale"], get_volume_fractions(model, "", "sld", params))
            self.assertListEqual(
                list(1-np.array(params["scale"])),
                get_volume_fractions(model, "", "sld_solvent", params)
            )

    def test_volfraction(self):
        """For 'volfraction' models make sure 'volfraction' parameter is being used."""
        params = {
            "scale": [0.05],
            "volfraction": [0.2],
        }
        self.assertListEqual(
            list(np.array(params["scale"])*np.array(params["volfraction"])),
            get_volume_fractions("fractal", "", "sld", params)
        )
        self.assertListEqual(
            list(1-np.array(params["scale"])*np.array(params["volfraction"])),
            get_volume_fractions("fractal", "", "sld_solvent", params)
        )

    def test_get_volume_fraction_binary_hard_sphere(self):
        params = {
            "scale": [0.5],
            "volfraction_lg": [0.2],
            "volfraction_sm": [0.4],
        }
        print(type(get_volume_fractions("binary_hard_sphere", "", "sld_lg", params)))
        self.assertAlmostEqual(
            params["scale"][0] * params["volfraction_lg"][0],
            get_volume_fractions("binary_hard_sphere", "", "sld_lg", params)[0]
        )
        self.assertAlmostEqual(
            params["scale"][0] * params["volfraction_sm"][0],
            get_volume_fractions("binary_hard_sphere", "", "sld_sm", params)[0]
        )
        self.assertAlmostEqual(
            1-params["scale"][0] * (params["volfraction_lg"][0] + params["volfraction_sm"][0]),
            get_volume_fractions("binary_hard_sphere", "", "sld_solvent", params)[0]
        )

    def test_get_volume_fraction_core_shell_sphere(self):
        radius = 60
        thickness = 10
        params = {
            "scale": [0.2],
            "radius": [radius],
            "thickness": [thickness],
        }
        inner = sphere_volume(radius)
        outer = sphere_volume(radius+thickness)
        core = inner/outer
        shell = (outer-inner)/outer
        self.assertAlmostEqual(core+shell, 1)
        self.assertAlmostEqual(
            core * params['scale'][0],
            get_volume_fractions("core_shell_sphere", "", "sld_core", params)[0]
        )
        self.assertAlmostEqual(
            shell * params['scale'][0],
            get_volume_fractions("core_shell_sphere", "", "sld_shell", params)[0]
        )
        self.assertAlmostEqual(
            1 - params['scale'][0],
            get_volume_fractions("core_shell_sphere", "", "sld_solvent", params)[0]
        )

    def test_get_volume_fraction_fractal_core_shell_sphere(self):
        radius = 60
        thickness = 10
        params = {
            "scale": [0.2],
            "radius": [radius],
            "thickness": [thickness],
            "volfraction": [0.5],
        }
        inner = sphere_volume(radius)
        outer = sphere_volume(radius+thickness)
        core = inner / outer
        shell = (outer - inner) / outer
        self.assertAlmostEqual(core + shell, 1)
        self.assertAlmostEqual(
            core * params['scale'][0] * params['volfraction'][0],
            get_volume_fractions("fractal_core_shell", "", "sld_core", params)[0]
        )
        self.assertAlmostEqual(
            shell * params['scale'][0] * params['volfraction'][0],
            get_volume_fractions("fractal_core_shell", "", "sld_shell", params)[0]
        )
        self.assertAlmostEqual(
            1 - params['scale'][0] * params['volfraction'][0],
            get_volume_fractions("fractal_core_shell", "", "sld_solvent", params)[0]
        )

    def test_get_volume_fraction_core_shell_cylinder(self):
        radius = 20
        thickness = 20
        length = 400
        params = {
            "scale": [0.2],
            "radius": [radius],
            "thickness": [thickness],
            "length": [length]
        }
        inner = cylinder_volume(radius, length)
        outer = cylinder_volume(radius+thickness, length + 2 * thickness)
        core = inner/outer
        shell = (outer-inner)/outer
        self.assertAlmostEqual(core+shell, 1)
        self.assertAlmostEqual(
            core * params['scale'][0],
            get_volume_fractions("core_shell_cylinder", "", "sld_core", params)[0]
        )
        self.assertAlmostEqual(
            shell * params['scale'][0],
            get_volume_fractions("core_shell_cylinder", "", "sld_shell", params)[0]
        )
        self.assertAlmostEqual(
            1 - params['scale'][0],
            get_volume_fractions("core_shell_sphere", "", "sld_solvent", params)[0]
        )

    def test_get_volume_fraction_core_shell_ellipsoid(self):
        radius_equatorial = 20
        radius_polar = 60
        thickness_equatorial = 10
        thickness_polar = 20
        params = {
            "scale": [0.2],
            "radius_equat_core": [radius_equatorial],
            "x_core": [radius_polar/radius_equatorial],
            "thick_shell": [thickness_equatorial],
            "x_polar_shell": [thickness_polar/thickness_equatorial],
        }
        inner = ellipsoid_volume(radius_polar, radius_equatorial)
        outer = ellipsoid_volume(radius_polar+thickness_polar, radius_equatorial+thickness_equatorial)
        core = inner/outer
        shell = (outer-inner)/outer
        self.assertAlmostEqual(core+shell, 1)
        self.assertAlmostEqual(
            core * params['scale'][0],
            get_volume_fractions("core_shell_ellipsoid", "", "sld_core", params)[0]
        )
        self.assertAlmostEqual(
            shell * params['scale'][0],
            get_volume_fractions("core_shell_ellipsoid", "", "sld_shell", params)[0]
        )
        self.assertAlmostEqual(
            1 - params['scale'][0],
            get_volume_fractions("core_shell_ellipsoid", "", "sld_solvent", params)[0]
        )

    def test_get_volume_fraction_core_multi_shell(self):
        radius = 200
        params = {
            "scale": [0.2],
            "n": [3],
            "radius": [radius],
            "thickness1": [40],
            "thickness2": [50],
            "thickness3": [60],
        }
        inner = (4/3)*np.pi*radius**3
        shells = []
        thickness = radius
        for i in range(1, params["n"][0]+1):
            thickness_n = params[f"thickness{i}"][0]
            shell = (4/3)*np.pi*((thickness_n+thickness)**3 - thickness**3)
            thickness += thickness_n
            shells.append(shell)
        total = inner + np.sum(shells)
        core = inner/total
        shells = np.array(shells)/total
        self.assertAlmostEqual(core + np.sum(shells), 1)
        self.assertAlmostEqual(
            params["scale"][0]*core,
            get_volume_fractions("core_multi_shell", "", "sld_core", params)[0]
        )
        for i in range(1, params["n"][0]+1):
            self.assertAlmostEqual(
                params["scale"][0]*shells[i-1],
                get_volume_fractions("core_multi_shell", "", f"sld{i}", params)[0]
            )
        self.assertAlmostEqual(
            1-params["scale"][0],
            get_volume_fractions("core_multi_shell", "", "sld_solvent", params)[0]
        )
