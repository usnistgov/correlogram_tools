[return to Home](./index.md)  
[return to Getting Started](./getting_started.md)

# Simulation Noise

The `sim_noise` section includes information of the noise that is desired in the simulated raw and reconstructed transmission and loss in viaibility
images due to the detector.

``` 
  "sim_noise": {

[//]: # (    "phase_step_sigma": 2.220446049250313E-16,)
    "moire_mean": 10000,
    "moire_vis": 0.3,
    "noise_mean": 0,
    "noise_var": 5.0E-7
  },
```

[//]: # (`phase_step_sigma`)

[//]: # (* The phase step error due to the displacement of linear stage in the phase stepping behavior &#40;float&#41;.)

[//]: # (* The value is the standard deviation of [normal distribution]&#40;https://www.mathworks.com/help/stats/normal-distribution.html&#41; with mean of 0.)

`moire_mean` and `moire_vis`
* The mean and visibility of Moire fringe applied to generate the simulated raw images (float).

`noise_mean` and `nosie_var`
* The quantized error added to the intensity of the simulaed raw images (float). 
* Values are mean and variance of [Gaussian noise](https://www.mathworks.com/help/images/ref/imnoise.html) approximates Poisson noise.
* The noise in simulated raw images propagates to reconstructed images. 



