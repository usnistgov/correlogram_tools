from pathlib import Path

import numpy as np
import PIL.Image

import periodictable.nsf as nsf
from sasmodels.bumps_model import Model
from sasmodels.core import load_model

from .sim_measurements import SimMeasurements
from .sim_models import SimModels
from . import hankel

ModelPars = dict[str, float | tuple[str, float]]
Vector = np.ndarray
Image = np.ndarray


def mixture_formula(param_dict: ModelPars) -> str:
    """
    Generates a combined component formula for mixture models to calculate transmission.

    The param_dict contains::
        {
            "scale": 1
            "A_scale": portion A,
            "A_sld": ("compound A", density A),
            "A_sld_solvent": ("solvent", density solvent),
            "B_scale": portion B,
            "B_sld": ("compound B", density B),
            "B_sld_solvent": ("solvent", density solvent),
            ...
        }

    or if there is only one component::
        {
            "scale": compound portion
            "sld": ("compound", density),
            "sld_solvent": ("solvent", solvent density),
        }

    Forms:

        A_percent%vol A@densityA // B_perent%vol B@densityB // ... // solvent@density solvent

    If scale is not one, then scale all portions by scale.
    """

    # Note: could use mix_by_volume(compound@density, vol, compound@density, vol, ...)
    # Not sure it makes the code that much cleaner.

    # PAK: Relying on sld_solvent in every model may not always work.
    # TODO: implement more robust approach

    comb_formula = ""
    for sld_param in [x for x in param_dict.keys() if 'sld' in x and 'solvent' not in x]:
        x_p = np.round(param_dict[sld_param][2] * 100, 2)
        comb_formula += f"{x_p}%vol {param_dict[sld_param][0]}@{param_dict[sld_param][1]} // "
    solvent_param = [x for x in param_dict.keys() if 'solvent' in x][0]
    comb_formula += f"{param_dict[solvent_param][0]}@{param_dict[solvent_param][1]}"
    return comb_formula


def get_penetration_depth(param_dict: ModelPars, wavelength: float) -> float:
    """
    The param_dict is a dictionary of parameter keywords : values, except for sld type parameters which are given as
    keyword : (formula, density, volume fraction). This function will create the full combined formula considering all
    components to calculate the penetration depth for the full sample (will be used to determine attenuation).

    Wavelength should be given in units of nm.
    """
    comb_formula = mixture_formula(param_dict)
    sld, xs, pen = nsf.neutron_scattering(comb_formula, wavelength=wavelength*10)
    return pen


def compute_sld(param_dict: ModelPars, wavelength: float) -> dict[str, float]:
    """
    Converts the keyword: (formula, density) pairs of sld type parameters into keyword: sld

    Wavelength should be given in units of nm.
    """

    temp_params = {}
    for param, value in param_dict.items():
        if 'sld' not in param:
            temp_params[param] = value
        else:
            temp_params[param] = nsf.neutron_scattering(value[0], density=value[1], wavelength=wavelength*10)[0][0]
    return temp_params


class SimExperiment(SimMeasurements, SimModels):
    """
    The Experiment class inherits the SimMeasurements and SimModels class to generate the simulated H0 and H1byH0 images
    from the defined measurement conditions (SimMeasurements) and models or structures of the regions of interest
    (SimModels).

    The simulated images are not automatically generated upon creation of an Experiment instance to manage computational
    expense. Therefore, the generate_simulated_images method should be called when those images are required.

    Attributes
    ----------
    H0 : array_like, height x width x N
        Simulated transmission image for N measurements or image acquisitions.
        From the Moiré pattern at the detector, this is determined by mean_sample / mean_open.
        The height and width correspond to the dimensions of the ROI mask provided with the experiment
        configuration file.
        The open beam or background regions of the image are automatically set to 1 (normalized image).
    H1byH0 : array_like, height x width x N
        Simulated loss in visibility image for N measurements or image acquisitions.
        From the Moiré pattern at the detector, this is determined by
        (amplitude_sample / mean_sample) / (amplitude_open / mean_open).
        The height and width correspond to the dimensions of the ROI mask provided with the experiment.
    export_path : str, filepath
        Absolute filepath to the export location for simulated H0 and H1byH0 images.
        This is the location of the configuration (.js) file where a new 'simulated_images' directory will be created.
    """
    H0: np.ndarray | None = None
    H1byH0: np.ndarray | None = None
    export_path: Path

    def __init__(self, config_path: Path | str):
        """
        Creates an instance of the Experiment class using the experiment configuration defined in a .js file.

        Parameters:
        -----------
        config_path : str, filepath
            Relative filepath to the simulation experiment configuration file (.js file).
        """
        super().__init__(config_path=config_path)
        self.export_path = self.mask_path.parent / "simulated_images"

    def apply_pen_mu_per_wavelength(
            self, penetration: Vector, mu: Vector, model_name: str, param_dict: ModelPars,
            wavelength: float) -> tuple[Image, Image]:
        """Applies the correct penetration length and dark_field for the specified wavelength in the measurements."""

        mask = np.where(self.measurements_wavelength == wavelength)[0]

        pen = get_penetration_depth(param_dict, wavelength)
        penetration[mask] = pen

        temp_params = compute_sld(param_dict, wavelength)
        kernel = load_model(model_name)
        model = Model(kernel, **temp_params)

        thickness = 1  # cm
        DF = hankel.sim_dark_field(
            self.measurements_xi*10,  # autocorrelation length for hankel is required in Angstroms
            model,
            wavelength*10,  # wavelength for hankel is required in Angstroms
            thickness).reshape(-1)
        mu[mask] = DF[mask]

        return penetration, mu

    def _get_penetration_depth_and_correlograms(self) -> tuple[dict[int, Image], dict[int, Image]]:
        """Calculate the penetration length and dark_field for each ROI and model at each wavelength."""

        penetration_roi = {}
        mu_roi = {}

        for roi, params in self.models.items():

            unique_wavelengths = np.unique(self.measurements_wavelength)

            # create templates for penetration depth and mu based on length of measurements
            penetration = np.ones_like(self.measurements_xi, dtype=float)
            mu = np.ones_like(self.measurements_xi, dtype=float)

            for wavelength in unique_wavelengths:
                penetration, mu = self.apply_pen_mu_per_wavelength(penetration, mu, params[0], params[1], wavelength)

            penetration_roi[roi] = penetration
            mu_roi[roi] = mu

        return penetration_roi, mu_roi

    def generate_simulation_images(self) -> None:
        """
        Creates the self.H0 and self.H1byH0 attributes which contain the simulated H0 and H1byH0 images for each
        measurement condition in self.measurements_*.
        """

        # TODO: these should be in their respective sim classes upon initialization
        # self.measurements = self.gen_measurements() CMW: added this to init of sim.measurements, 12-6-2022
        self.models = self.setup_models()

        penetration_roi, mu_roi = self._get_penetration_depth_and_correlograms()

        mask_path = self.mask_path
        thickness_path = self.thickness_path
        mask = np.array(PIL.Image.open(mask_path))
        thick = np.array(PIL.Image.open(thickness_path))

        H0 = np.ones((mask.shape[0], mask.shape[1], len(self.measurements_xi)))
        for roi, p in penetration_roi.items():
            roi_loc = np.where(mask == int(roi))
            H0[roi_loc[0], roi_loc[1], :] = np.exp(-thick[roi_loc[0], roi_loc[1], None] / p[None, None, :])

        H1byH0 = np.ones((mask.shape[0], mask.shape[1], len(self.measurements_xi)))
        for roi, mu in mu_roi.items():
            roi_loc = np.where(mask == int(roi))
            H1byH0[roi_loc[0], roi_loc[1], :] = np.exp(-mu[None, None, :] * thick[roi_loc[0], roi_loc[1], None])

        self.H0 = np.float32(H0)
        self.H1byH0 = np.float32(H1byH0)
