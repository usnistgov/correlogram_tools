"""
This script will interpret the provided simulation experiment configuration (.js) file and generated simulated H0 and
H1byH0 INFER images along with a nexus file describing the experiment and measurement conditions for each image.

Usage example:

    python -m correlogram_tools.simulation examples/paperp_figures/input_paper.json

Creates:

    correlogram_tools/tests/simulation_example/sphere_example.nxs

See correlogram_tools/sim_template.js for an annotated example of the
experiment definition format.
"""
import argparse

from . import sim_experiment
from .sim_images import create_images
# from . import nexus_tools
from . import sim_moire

# Using command line parser since we will eventually want more control
parser = argparse.ArgumentParser(description='Run infer simulation.')
parser.add_argument(
    '-r', '--reconstruct', action='store_true',
    help='Simulate moire projections and reconstruction')
parser.add_argument(
    '-f', '--format', type=str, default='tiff',
    help='Produce images the given extension (tiff, png, etc.)')
# parser.add_argument(
#     '-s', '--saveraw', action='store_false',
#     help='Save raw projections during simulation')
parser.add_argument(
    'filename', type=str,
    help='experiment description')


def main():
    args = parser.parse_args()

    experiment = sim_experiment.SimExperiment(args.filename)
    experiment.generate_simulation_images()
    # turning off nexus tools until future review and versions
    # nexus_tools.create_nexus(experiment, ext=args.format)
    create_images(experiment, ext=args.format)
    if args.reconstruct:
        save_raw = True
        sim_moire.sim_moire(experiment, save_raw=save_raw, ext=args.format)


if __name__ == "__main__":
    # from bumps.util import profile; profile(main)
    main()
