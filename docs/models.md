[return to Home](./index.md)  
[return to Getting Started](./getting_started.md)

# Models

The `models` section outlines the specifics of the microstructure for each ROI by specifying the parameters
of the relevant SasView model.

An example of the `models` section for a sample scene with 4 ROI's is shown below. It is comprised of a list in which
each item in the list describes either a unique ROI or similar ROI's grouped together. The `roi` keyword is used to
delcare the integer label from the ROI mask that the model information applies to. It should be formatted as a list of
integers. The `intent` keyword is used to designate the ROI's as either the open/background of the scene or a sample
using the `open` and `sample` labels, respectively.

```
 "models": [
    {
      "roi": [4],
      "intent": "open"
    },
    {
      "roi": [1, 2],
      "intent": "sample",
      "model": {
        "model_mode": "user-defined",
        "model_name": "sphere",
        "model_parts": [
          {
            "part_name": "sphere",
            "parameters": {
              "radius": {
                "parameter_mode": "user-defined",
                "value": [
                  250, 375, 500
                ]
              },
              "radius_pd": {
                "parameter_mode": "user-defined",
                "value": [
                  0.1
                ]
              },
              "scale": {
                "parameter_mode": "user-defined",
                "value": [
                  0.1
                ]
              }
            },
            "sample_components": {
              "sld": {
                "component_mode": "molecular-formula",
                "value": "C8H8",
                "density": 1.05
              },
              "sld_solvent": {
                "component_mode": "molecular-formula",
                "value": "D2O",
                "density": 1.1
              }
            }
          },
        ]
      }
    },
    {
      "roi": [3],
      "intent": "sample",
      "model": {
        "model_mode": "user-defined",
        "model_name": "sphere@hardsphere",
        "model_parts": [
          {
            "part_name": "sphere",
            "parameters": {
              "radius": {
                "parameter_mode": "user-defined",
                "value": [
                  500
                ]
              },
              "radius_pd": {
                "parameter_mode": "user-defined",
                "value": [
                  0.1
                ]
              },
              "scale": {
                "parameter_mode": "user-defined",
                "value": [
                  1
                ]
              }
            },
            "sample_components": {
              "sld": {
                "component_mode": "molecular-formula",
                "value": "C8H8",
                "density": 1.05
              },
              "sld_solvent": {
                "component_mode": "molecular-formula",
                "value": "(D2O)11(H2O)3",
                "density": 1.079
              }
            }
          },
          {
            "part_name": "hardsphere",
            "parameters": {
              "volfraction": {
                "parameter_mode": "user-defined",
                "value": [
                  0.1
                ]
              },
              "radius_effective": {
                "parameter_mode": "user-defined",
                "value": [500]
              }
            },
            "sample_components": {
              "sld": {
                "component_mode": "molecular-formula",
                "value": "C8H8",
                "density": 1.05
              },
              "sld_solvent": {
                "component_mode": "molecular-formula",
                "value": "(D2O)11(H2O)3",
                "density": 1.079
              }
            }
          }
        ]
      }
    },
```

## Open or Background ROI
___
For the open or background ROI, only the `roi` and `intent` keywords are required and used. Any other information is
discarded. Note that only a single ROI can be used for all open spaces in the sample scene.

```
 "models": [
    {
      "roi": [4],
      "intent": "open"
    },
    {...},
    {...},
 ]
```

## Sample ROI's
___

The sample ROI's can be grouped together if they have similar microstructures. For example, a series of spherical
particles in water that varies in concentration would only require a single parameter to scan.

```
 "models": [
    {...},
    {
      "roi": [1, 2],
      "intent": "sample",
      "model": {
        "model_mode": "user-defined",
        "model_name": "sphere",
        "model_parts": [
          {...}
        ]
      }
    },
    {...},
```
### `model`

The model section defines the microstructure for the ROI(s) listed. The `model_mode` should be set as `user-defined`. In
the future more functionality will be added to select models at random.

The `model_name` specifies which SasView model describes the microstructure. Currently only a subset of the SasView 
models are accepted but as development continues, the `correlogram-tools` pacakge will expand to include the over 70
models available in SasView. The models currently accepted include:
* core_shell_cylinder
* core_shell_ellipsoid
* core_shell_sphere
* cylinder
* ellipsoid
* hardsphere
* hayter_msa
* sphere
* squarewell
* stickyhardsphere

The models and their names can be found in the SasView 
[documentation](https://www.sasview.org/docs/user/qtgui/Perspectives/Fitting/models/index.html). The form factors can be
used individually or summed together, e.g., both `sphere` and `sphere1+sphere2` are accepted. Note that a single digit 
identifier should be included at the end of the individual model names when using a combined model with duplicate form
factors. This is to pair each component of the model to the appropriate entry in the `model_parts` section. If a 
structure factor is being used, it should be combined with the appropriate form factor as `sphere@hardsphere`.

### `model_parts`

The `model_parts` section is defined as a list of parameter definitions for each unique SasView model in the declared
`model_name`. 

```
        "model_parts": [
          {
            "part_name": "sphere",
            "parameters": {
              "radius": {...},
              "radius_pd": {...},
              "scale": {...}
            },
            "sample_components": {
              "sld": {...},
              "sld_solvent": {...}
            }
          },
        ]
```

The `part_name` should match with a single component of the `model_name`. In this example above, only a `sphere` model
is being used. However, if a `sphere1+sphere2` model was declared, there would be 2 entries in the `model_parts` list.
The first would have a `part_name` of `sphere1` and the second would have a `part-name` of `sphere2`.

The `parameters` section declares the values of all non-scattering length density (SLD) type parameters. For example, the 
[sphere](https://www.sasview.org/docs/user/models/sphere.html) model would need to declare parameters of `scale` and 
`radius`. No `background` parameters are ever accepted as these do not translate to the dark field space from the small-
angle scattering space. If the `background` is set, then it will be ignored and set to 0. 

The SLD-type parameters of `sld` and `sld_solvent` are set in the `sample_components` section. The SLD is not set
directly but rather molecular information is provided so that the transmission and SLD can both be calculated internally
in the simulator.

### Parameters

Similar to the parameters of the `measurements` section, the values of the model parameters are set using various 
parameter modes and values.

``` 
              "radius": {
                "parameter_mode": "user-defined",
                "value": [
                  250, 375, 500
                ]
              }
```

The following parameter modes can be used:

#### `range`
  ``` 
  "mode": "range",
  "value": [start (float), stop (float), N (int), type (str)],
  ```
* Generates a range of values from the start and stop (inclusive) with N number of points.
* A log or linear spacing can be set using a type of "log" or "linear" respectively.
* Example: `[1, 10, 10, "linear"]` will generate values of `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]`
* Example: `[1e0, 1e4, 5, "log"]` will generate values of `[1, 10, 100, 1000, 10000]`

#### `user-defined`
  ``` 
  "mode": "user-defined",
  "value": [value1 (float), value2 (float), ... , valueN (float)],
  ```
* Sets custom values of the parameter directly.
* N should either be equal to 1 (variable is the same value for all ROIs) or equal to the number of ROIs

#### `random-single`
  ``` 
  "mode": "random-single",
  "value": [min (float), max (float)],
  ```
* Selects a single random value from the range specified by the min and max values.
* If no value is specified, the default bounds for the parameter are used.
* The same value will be used for all ROI's defined by this model.

#### `random`
  ``` 
  "mode": "random",
  "value": [min (float), max (float)],
  ```
* Selects a random value from the range specified by the min and max values for each ROI defined by this model.
* If no value is specified, the default bounds for the parameter are used.

### Sample Components

The SLD is not set  directly but rather molecular information is provided so that the transmission and SLD can both be 
calculated internally. The sample component can be set with the `molecular-formula` or the `component-library` keyword.

``` 
              "sld": {
                "component_mode": "molecular-formula",
                "value": "C8H8",
                "density": 1.05
              },
              "sld_solvent": {
                "component_mode": component-library",
                "value": "deuterium_oxide"
              }
```

#### `molecular-formula`
* This mode requires that the molecular formula be provided as the `value` as well as the `density`.

#### `component-library`
* A small number of materials are provided in a component library and can be referenced by name.
* The molecular formula and density are instead extracted from the component library.
* Currently, only `polystyrene`, `deuterium_oxide`, and `water` are avialble but this will be expanded in the future.

#### `random-single`
  ``` 
  "mode": "random-single",
  "value": [min (float), max (float)],
  ```
* Selects a single random value from the range specified by the min and max values.
* If no value is specified, the default bounds for the parameter are used.
* The same value will be used for all ROI's defined by this model.

#### `random`
  ``` 
  "mode": "random",
  "value": [min (float), max (float)],
  ```
* Selects a random value from the range specified by the min and max values for each ROI defined by this model.
* If no value is specified, the default bounds for the parameter are used.
