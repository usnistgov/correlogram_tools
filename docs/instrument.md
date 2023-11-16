[return to Home](./index.md)  
[return to Getting Started](./getting_started.md)

# Instrument

The `instrument` section includes details of the instrument configuration such as interferometer length, pixel pitch of
the detector, aperture sizes and the phase stepping behavior of the phase gratings. The parameters are used for the geometric magnification and blur of simulated raw images.

``` 
  "instrument": {
    "interferometer_length": 6,
    "x_pixel_pitch": 50,
    "y_pixel_pitch": 50,
    "slit_aperture_x": 10,
    "slit_aperture_y": 10,
    "n_phase_steps": 10,
    "n_phase_step_periods": 2
  },
```
`interferometer_length`
* The distance from the aperture to detector in units of meters.

`x_pixel_pitch` and `y_pixel_pitch`
* The pixel pitch in x- and y-direction of the detector in units of micrometers. This is the effective pixel size of simulated raw and reconstructed transmission and loss in visbility images. 

`slit_aperture_x` and `slit_aperture_y`
* The source slit size in x- and y-direction in units of centimeters.
* The aperture is assumed as a circular aperture in the geometric blur, and the slit size is the radius of circular aperture. 

`n_phase_steps`
* The number of phase step positions one of the phase gratings will translate (integer). For example, the number of phase step position in figure is 10. 

`n_phase_step_periods`
* The number of Moire periods the phase grating will step across (float). For example, the number of Moire periods in figure is 1.5. 

<img src="/data/images/PhaseSteppedIntensity.png" alt="drawing" width="60%"/>
