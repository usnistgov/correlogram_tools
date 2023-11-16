"""
This code is for image writing during the simulation. It replaces nexus_tools.py until nexus functionality is
returned to the simulation.
"""

import os

import numpy as np
from PIL import Image

from .sim_experiment import SimExperiment


def create_images(experiment: SimExperiment, ext: str = 'tif') -> None:
    """
    Exports the H0 and H1byH0 simulated images for a simulation experiment which is
    and instance of the class SimExperiment.
    """
    # TODO: don't mix simulation and file I/O in the same function.
    if experiment.H0 is None or experiment.H1byH0 is None:
        # raise RuntimeError("No data to save for the experiment.")
        experiment.generate_simulation_images()

    os.makedirs(experiment.export_path, exist_ok=True)
    xi = experiment.measurements_xi
    period = experiment.measurements_moire
    wavelength = experiment.measurements_wavelength
    z = experiment.measurements_z
    index = np.arange(1, len(xi)+1)

    measurement_details = np.vstack((index, xi, period, wavelength, z)).T
    measurement_file = os.path.join(experiment.export_path, 'measurement_details.csv')
    np.savetxt(
        measurement_file, measurement_details, fmt=('%d', '%1.3f', '%1.3f', '%1.3f', '%1.3f'), delimiter=',',
        header='measurement number, xi (nm), period (mm), wavelength (nm), z (mm)',
        )

    # Note: This throws away multiple extensions, like "*.js.txt". Should be okay.
    nexus_basename = os.path.basename(experiment.config_path).split('.')[0]

    # Generate H0 and H1byH0 images in the export directory.
    for k in range(experiment.H0.shape[-1]):
        stem = xi_encode(nexus_basename, xi=xi[k], period=period[k]*1000, wavelength=wavelength[k], z=z[k])
        H0 = experiment.H0[:, :, k]
        H0_path = f"{stem}_H0.{ext}"
        imsave(H0, experiment.export_path / H0_path, peak=1.1)

        H1byH0 = experiment.H1byH0[:, :, k]
        H1byH0_path = f"{stem}_H1byH0.{ext}"
        imsave(H1byH0, experiment.export_path / H1byH0_path, peak=1.1)


def xi_encode(base, xi=None, period=None, z=None, wavelength=None, phase=None, increment=None):
    """
    Build filename from base name plus encoded xi, period, z, wavelength, phase and increment.
    """
    stem = base
    if xi is not None:
        stem += f"_xi{int(xi):04d}"
    if period is not None:
        stem += f"_P{int(period):04d}"
    for part in (z, wavelength, phase):
        if part is not None:
            stem += "_" + _num_encode(part)
    if increment is not None:
        stem += f"_{increment:06d}"
    return stem


def _num_encode(v):
    s = f"{v:+08f}".replace('+', 'p').replace('-', 'm').replace('.', 'd')
    return s


def imsave(data, path, peak=1.1):
    if path.suffix.lower() not in ('tif', 'tiff'):
        data = (np.clip(data, 0, peak)*(65535/peak)).astype('uint16')
    data = Image.fromarray(data)
    data.save(path)
