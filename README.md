# correlogram-tools

This project includes tools to simulate 1D and 2D dark field interferometry data in real space for the 
[INFER](https://www.nist.gov/programs-projects/interferometry-infer-neutron-interferometric-microscopy-small-forces-and) 
project and simultaneously compare with small-angle scattering data in Fourier space. It utilizes existing form factor and 
structure factor models as well as the existing numerical implementation of the Hankel transform in the 
`sasmodels` package located at https://github.com/SasView/sasmodels in order to:
- generate simulated dark field and attenuation images that include optical corrections for specific instrumentation
- interactively and simultaneously simulate SANS and dark field 1D spectra


## Theory and Definitions

One of the goals of the 
[INFER](https://www.nist.gov/programs-projects/interferometry-infer-neutron-interferometric-microscopy-small-forces-and) 
project is to develop a grating-based far field neutron interferometer to collect spatially-resolved structural 
information at the same length scales as small-angle neutron scattering (SANS) from 1 nm to 10 $`\mu`$m. A simplified schematic diagram of 
a 2-grating far field interferometer is shown in the image below. The neutron source starts at the source slit location 
and passes through two phase gratings with the same period, $`P_{G1}=P_{G2}`$ before reaching the detector position. The 
gratings result in a Moire pattern across the detector with a period of $`P_D`$ which can be determined by the phase 
grating period, the source-to-detector distance, $`L`$, and the distance between phase gratings, $`D`$. The instrument 
probes structural features within the sample at a length scale of $`\xi`$, which is defined as the autocorrelation 
length and can be determined by the sample-to-detector distance, $`Z`$, the neutron wavelength, $`\lambda`$, and the 
period of the Moire pattern, $`P_D`$. 

<img src="/data/images/GratingInterferometer.png" alt="drawing" width="60%"/>

When a sample is placed in the beam path, small-angle scattering due to structural features at the probed 
autocorrelation length, $`\xi`$, result in a loss in visibility of the sinusoidal Moire pattern at the detector. This loss in visibility can be calculated from the mean, $`(A)`$, and amplitude, $`(B)`$, of the Moire pattern from a sample measurement and open beam measurement. The mean values can be used to first reconstruct a normalized transmission image, $`H_0`$:

```math
H_0=\frac{A_{sample}}{A_{open}}
```

Similarly, the amplitude values can be used to reconstruct a normalized amplitude image, $`H_1`$:

```math
H_1=\frac{B_{sample}}{B_{open}}
```

Finally, $`H_0`$ and $`H_1`$ can be used to reconstruct the loss in visibility, 
$`\frac{V_s}{V_o}`$:

```math
\frac{V_s}{V_o} = \frac{H_1}{H_0}
```

This dark field intensity, $`DF`$, is related to the and structural features in the sample by:

```math
DF(\xi) = -ln(\frac{V_s}{V_o}) = -\lambda^2 t(G(\xi)-G_0)
```

where $`t`$ is the sample thickness and $`G`$ is the projection function of the autocorrelation function, which is 
related to the scattering cross-section, $`I(q)`$, through the following Hankel transformation:

```math
G(\xi) = \frac{1}{2\pi}\int^\infty_0 J_0(q\xi)I(q)qdq
```

```math
G_0 = \frac{1}{2\pi}\int^\infty_0 I(q)qdq
```

where $`J_0`$ is the zeroth order Bessel function of the first kind and $`q`$ is the scattering vector. The scattering 
cross-section is defined as:
```math
I(q) = \phi\Delta\rho^2P(q)S(q)
```
where $`\phi`$ is the volume fraction of scatterers, $`\Delta\rho^2`$ is the contrast, or difference in scattering 
length density squared between the scatterer and background/solvent, $`P(q)`$ is the form factor which includes information about the size and shape of the scatterer, and $`S(q)`$ is the structure factor which includes information about the correlations or interactions between scatterers. 

## Installation

A Python installation is required to utilize `correlogram-tools`. If you do not yet have Python installed on your 
system, you can do so by installing a package manager such as 
[Anaconda](https://www.anaconda.com/products/individual#Downloads). Create a new Python environment. If using conda,
one can use the following command to create and activate the environment:
```
conda create -n correlograms python=3.10
conda activate correlograms
```
Navigate to the `correlogram-tools` directory and install the package and required dependencies with:
```
pip install .
```

## Usage

Read more about different ways to use `correlogram-tools` in the [documentation](./docs/index.md).

## Contributors

- Caitlyn Wolf, NIST Center for Neutron Research, NIST, caitlyn.wolf@nist.gov 
- Paul Kienzle, NIST Center for Neutron Research, NIST
- Youngju Kim, Physical Measurement Laboratory, NIST
- Pushkar Sathe, Information Technology Laboratory, NIST
- M. Cyrus Daugherty, Physical Measurement Laboratory, NIST
- Peter Bajcsy, Information Technology Laboratory, NIST
- Daniel Hussey, Physical Measurement Laboratory, NIST
- Katie Weigandt, NIST Center for Neutron Research, NIST

Please contact Caitlyn Wolf at the email above with any questions or comments regarding this code.
