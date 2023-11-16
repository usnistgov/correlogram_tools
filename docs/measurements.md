[return to Home](./index.md)  
[return to Getting Started](./getting_started.md)

# Measurements

The `measurements` section includes details of the autocorrelation lengths at which the images should be generated and 
requires information about the Moire period, sample to detector distance, and wavelength, in order to simulate both 
the theoretical images from the small-angle scattering models but also the raw and reconstructed images that include
effects such as magnification as one modulates the sample to detector distance.

An example of the `measurements` section:
```
  "measurements": [
    {
      "measurement_mode": "multi-scan",
      "xi": {
        "mode": "calculated"
      },
      "moire": {
        "mode": "discrete",
        "value": [0.2, 0.4, 1.0],
        "units": "mm"
      },
      "z": {
        "mode": "discrete",
        "value": [50, 125, 250],
        "units": "mm"
      },
      "wavelength": {
        "mode": "fixed",
        "value": [4],
        "units": "Ang"
      }
    }
  ],
```

## Measurement Modes

The `measurement_mode` declares which type of measurement scan will be simulated, i.e., how the parameters of Moire
period (`moire`), sample to detector distance (`z`), and wavelength (`wavelength`) will be modulated to access the range
of requested autocorrelation lengths (`xi`). Each `measurement_mode` has different requirements for the parameter mode 
and values set for each of the `moire`, `z`, `wavelength`, and `xi` parameters.

The following keywords are accepted for `measurement_mode`:

### xi-scan
* The autocorrelation lengths, `xi`, are set using a parameter mode of `range` or `discrete`.
* All other parameters are set at values that achieve the specified autocorrelation lengths using the following options:
  * `wavelength` is set at a `fixed` mode
  * One of `moire` or `z` should be set at a `fixed` or `discrete` mode and the other at a `continuous` mode
* Example:
  ```  
  "measurements": [
    {
      "measurement_mode": "multi-scan",
      "xi": {
        "mode": "discrete",
        "value": [50, 100, 150, 200],
        "units": "nm"
      },
      "moire": {
        "mode": "discrete",
        "value": [0.2, 0.4, 1.0],
        "units": "mm"
      },
      "z": {
        "mode": "continuous",
        "value": [30, 300],
        "units": "mm"
      },
      "wavelength": {
        "mode": "fixed",
        "value": [4],
        "units": "Ang"
      }
    }
  ],
  ```
  The conditions above will result in the following measurement points:

    | Measurment | Xi | Moire  |  Z   | Wavelength |
    | :----: |:------:|:----:| :----: | :----: |
    | 1 | 50  |  0.4   |  50  | 4 |
    | 2 | 100 |  0.2   |  50  | 4 |
    | 3 | 150 |  0.2   |  75  | 4 |
    | 4 | 200 |  0.2   | 100  | 4 |


* If some autocorrelation lengths are impossible within the constraints of other parameters, the simulator will return a warning and only generate images at the accepted autocorrelation lengths.

### z-scan
* The sample to detector distance `z` is modulated to achieve different autocorrelation lengths or `xi`.
* The `z` parameter is set with either a `range` or `discrete` mode.
* Both `wavelength` and `moire` are set to a `fixed` parameter mode.
* The autocorrelation length `xi` is set to a `calculated` mode.
* Example:
  ```  
  "measurements": [
    {
      "measurement_mode": "z-scan",
      "xi": {
        "mode": "calculated",
        "units": "nm"
      },
      "moire": {
        "mode": "fixed",
        "value": [0.8],
        "units": "mm"
      },
      "z": {
        "mode": "range",
        "value": [50, 80, 4, "linear"],
        "units": "mm"
      },
      "wavelength": {
        "mode": "fixed",
        "value": [4],
        "units": "Ang"
      }
    }
  ],
  ```
  The conditions above will result in the following measurement points:

    | Measurement | Xi     | Moire |  Z   | Wavelength |
    | :----: | :----: |:----:| :----: | :----: |
    | 1 | 25 | 0.8    |  50  | 4 |
    | 2 | 30 | 0.8    |  60  | 4 |
    | 3 | 35 | 0.8    |  70  | 4 |
    | 4 | 40 | 0.8    |  80  | 4 |

### wavelength-scan
* The `wavelength` is modulated to achieve different autocorrelation lengths or `xi`.
* The `wavelength` parameter is set with either a `range` or `discrete` mode.
* Both `z` and `moire` are set to a `fixed` parameter mode.
* The autocorrelation length `xi` is set to a `calculated` mode.
* This mode is similar to the `z-scan` above but changes the modulated parameter.

### moire-scan
* The `moire` is modulated to achieve different autocorrelation lengths or `xi`.
* The `moire` parameter is set with either a `range` or `discrete` mode.
* Both `wavelength` and `moire` are set to a `fixed` parameter mode.
* The autocorrelation length `xi` is set to a `calculated` mode.
* This mode is similar to the `z-scan` and `wavelength-scan` above but changes the modulated parameter.

### multi-scan
* This scan is similar to the previous three but any of the `wavelength`, `moire`, or `z` parameters can be allowed to vary.
* The parameters selected to vary are defined with a `range` or `discrete` mode. All others are set at `fixed`.
* The autocorrelation length `xi` is set to a `calculated` mode.
* The simulator will generate an image at every combination of values in the scan, so this can quickly become large. Ten scan points for three variables would generate 1000 transmission and 1000 loss in visilibity images.

### custom-scan
* The mode enables a fully flexibly set of measurement conditions.
* The autocorrelation length `xi` is set to a `calculated` mode.
* All remaining parameters are set to a `file` mode that lists the value for each variable in a separate file.
* Each row in each of the files corresponds to the same measurement.

## Parameter Units

The units for any of the parameters can be set using the `units` keyword, however, currently the only accepted units are:
* `nm` for `xi`
* `mm` for `moire`
* `mm` for `z`
* `Ang` for `wavelength`

Providing any of the parameters in units other than the accepted ones above will result in an error. If no units are
listed, the simulator will assume the accepted units above. In the future this will be expanded to perform unit 
conversions as necessary.

## Parameter Modes
___
Each parameter is required to be set with a `mode` and potentially a corresponding `value` and `units` pair. The
available modes include:

### Range
  ``` 
  "mode": "range",
  "value": [start (float), stop (float), N (int), type (str)],
  ```
* Generates a range of values from the start and stop (inclusive) with N number of points.
* A log or linear spacing can be set using a type of "log" or "linear" respectively.
* Example: `[1, 10, 10, "linear"]` will generate values of `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]`
* Example: `[1e0, 1e4, 5, "log"]` will generate values of `[1, 10, 100, 1000, 10000]`

### Fixed
  ``` 
  "mode": "fixed",
  "value": [value1 (float)],
  ```
* Sets the parameter at a single fixed value (`value1`).

### Discrete
  ``` 
  "mode": "discrete",
  "value": [value1 (float), value2 (float), value3 (float), ..., valueN (float)],
  ``` 
* Defines a list of N number of acceptable values of the parameter.

### Continuous
  ``` 
  "mode": "continuous",
  "value": [minimum (float), maximum (float)],
  ```
* Defines an acceptable value range of the parameter.

### Calculated
* Indicates that this parameter should be determined based on the values of the other measurement parameters.
* This mode does not require a `value` to be set and therefore, limits on the parameter cannot be place.

### File
  ``` 
  "mode": "file",
  "value": "./relative/path/to/file.txt",
  ```
* The value of the parameter for each measurement point is specified in a file.
* The file is a single column text file with no headers or other information besides the specified values.
