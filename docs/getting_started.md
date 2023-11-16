[return to Home](./index.md)
# Getting Started

The `correlogram-tools` package can be used in three primary ways:
1. Generate simulated raw and reconstructed transmission and dark field images via the [**command line**](#1-command-line-simulation).
2. Simultaneously plot theoretical small-angle scattering models in both the dark field and small-angle scattering spaces with the Jupyter Notebook [**plotting widget**](#2-plotting-widget).
3. Generate simulated one-dimensional data by Python [**scripting**](#3-scripting).

## 1. Command Line Simulation

The command line simulation enables one to generate raw and reconstructed transmission and dark field images from a 
dark field interferometry experiment. Currently, this is package only simulates radiography measurements. In the future,
this will be expanded to tomography. The user specifies at which autocorrelation lengths data is collected and a
transmission and loss in visibility is produced at each length scale. The sample 'scene' is defined by the region of
interest (ROI) mask in which each ROI represents a unique microstructure. The thickness or pathlength through the sample
at each pixel location is defined with the thickness mask.

It requires three inputs (1) json-formatted input file, (2) region of interest (ROI) mask, and (3) thickness or 
pathlength mask. A directory will be created at the location of the input file called `simulated images` and will 
include the transmission and loss in visibility images for each autocorrelation length specified, and a csv-formatted 
measurement summary that lists the autocorrelation length, Moire period, sample to detector distance, and wavelength 
for each image produced.

When the simulation control files are ready the program can be run using:
```
python -m correlogram_tools.simulation [-r] [-f tiff] input.json
```
This outputs the predicted transmission and visibility images for each instrument configuration.
The `-r` option generates the simulated Moiré patterns with effects such as statistical noise and geometric blur as well as the reconstructed transmission and visibility.
The `-f` option selects the format of the image files (e.g., tiff, png, jpeg).
Use `-h` for a complete list of options.

### JSON-Formatted Input File

The JSON-formatted input file includes various sections that define the simulated experiment including measurement and
instrument details as well as the microstructural information for each ROI. The following sections are briefly described
here but is also linked to another page with more details.

The outermost level of the json input file is the `experiment`:
```
{"experiment": {
  "title": "Experiment title.",
  "description": "Any additional information about the simulated experiment.",
  "mask_path": "./relative/path/from/input/to/roi_mask.tif",
  "thickness_path": "./relative/path/from/input/to/thickness_mask.tif",
  "measurements": [...],
  "instrument": {...},
  "sim_noise": {...},
  "models": [...]
}}
```
The [`measurements`](./measurements.md) section includes details of the autocorrelation lengths at which the images should be generated and 
requires information about the Moire period, sample to detector distance, and wavelength, in order to simulate both 
the theoretical images from the small-angle scattering models but also the raw and reconstructed images that include
effects such as magnification as one modulates the sample to detector distance. More details can be found 
[here](./measurements.md).

The [`instrument`](./instrument.md) section includes details of the instrument configuration such as interferometer length, pixel pitch of
the detector, aperture sizes and the phase stepping behavior of the phase gratings. More details can be found 
[here](./instrument.md).

The [`sim_noise`](./sim_noise.md) section includes information of the noise that is desired in the simulated raw and reconstructed
images due to the detector. More details can be found [here](./sim_noise.md).

Finally, the [`models`](./models.md) section outlines the specifics of the microstructure for each ROI by specifying the parameters
of the relevant SasView model. More details can be found [here](./models.md).

### ROI Mask

The ROI mask is used to create the sample scene, i.e., the image of your sample array collected at the detector. The
tif image should be set at the sample resolution of the detector and each pixel includes a single integer value. Each
integer value corresponds to an ROI label in the `models` section of the input file. Note, there can only be a single
ROI integer specified for all the open area or background in the sample scene.

### Thickness Mask

The thickness mask is used to define the sample thickness or pathlength at each pixel location in units of centimeters.
The open or background ROI should be set with a thickness of 0. The thickness for a single ROI is not required to be
uniform so one can simulate images for a sample with non-uniform thickness throughout.

## 2. Plotting Widget


To use the graphical interface you will need to run in a jupyter notebook.
You can install and run a notebook server in your environment using:
```
pip install jupyter
jupyter notebook
```

The plotting widget can be launched in any notebook with the following two lines:
``` 
import correlogram_tools.plotting_widget as pw
pw.show_plotting_widget()
```
<img src="/data/images/PlottingWidget.png" alt="drawing" width="60%"/>

A notebook template has already been created with this code [here](../plotting_widget.ipynb). 

NB: plotly 5.18.0 doesn't work with older versions of jupyterlab.
You may need to downgrade using:
```
pip install plotly==5.15.0
```

## 3. Scripting

The `correlogram-tools` package can by imported as a Python library and used via scripting or in a Jupyter notebook.
To import the package use:
```
import correlogram_tools
```
