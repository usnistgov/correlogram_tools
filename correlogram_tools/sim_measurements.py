"""
Interpret the measurements section of the experiment structure, turning a set
of scans into a set of individual (xi, moire, wavelength, z) points.
"""

import numpy as np

from .sim_config import SimConfig

accepted_units = {  # accepted units for the simulation program
    "moire": "mm",
    "wavelength": "Ang",
    "xi": "nm",
    "z": "mm",
}


def check_units(keyword: str, units: str) -> None:
    """Raises an error if the units supplied for the keyword variable do not match the acceptable units of the
    simulation program."""
    if accepted_units[keyword] != units:
        raise Exception(f"Units of {units} are not accepted for {keyword}, only {accepted_units[keyword]} are "
              f"accepted.")


def range_interpreter(value: list) -> np.ndarray:
    """
    Interprets the settings for a variable specified in the experiment config with a mode of "range" and returns
    the values for that range.

    Parameters
    ----------
    value : list
        The value paired with a "range" mode for variables in the experimental configuration file.
        It will be formatted as a list: [start (float), stop (float), N (int), type (str)].
         - start and stop are the inclusive beginning and end points of the range
         - N is the number of points in the range
         - type is either "log" or "linear" which specifies the spacing of the range
    """

    if not (len(value) == 4
            and isinstance(value[0], (float, int))
            and isinstance(value[1], (float, int))
            and isinstance(value[2], int)
            and value[3] in ("log", "linear")):
        raise Exception(f"Incorrect value and types for range; the range format should be: "
                        f"[start (float), stop (float), N (int), type (str)]"
                        f" where type is either 'linear' or 'log'.")

    start, stop, N, scale = value
    if scale == "log":
        values = np.logspace(np.log10(start), np.log10(stop), num=N)
    else:
        values = np.linspace(start, stop, num=N)
    return values


def check_lengths(variable_list: list[np.ndarray | None]):
    """Raises an error if variable lengths do not match."""
    # PAK: previous code would fail if any variable was None because lengths would be too short
    maxlen = max(len(x) for x in variable_list if x is not None)
    for variable in variable_list:
        # Setting None to length 1 so that it gets ignored.
        size_k = len(variable) if variable is not None else 1
        if size_k != maxlen and size_k != 1:
            raise Exception(f"Instrument variables do not match in length (or equal 1).")


def get_missing_variable(
    keyword: str, 
    xi: np.ndarray | None = None,
    moire: np.ndarray | None = None,
    wavelength: np.ndarray | None = None,
    z: np.ndarray | None = None,
):
    """
    Calculates the variable specified in keyword based on other values in xi = wavelength * z / moire.
    Variables should be 1-D arrays with all the same length or length of 1.

    Units of the variables should be:
        xi: nm
        moire: mm
        wavelength: nm
        z: mm
    """

    if xi is not None:
        xi = np.asarray(xi, float).flatten()
    if moire is not None:
        moire = np.asarray(moire, float).flatten()
    if wavelength is not None:
        wavelength = np.asarray(wavelength, float).flatten()
    if z is not None:
        z = np.asarray(z, float).flatten()
    check_lengths([xi, moire, wavelength, z])

    try:
        if keyword == "xi":
            value = wavelength * z * np.reciprocal(moire)
        elif keyword == "wavelength":
            value = xi * moire * np.reciprocal(z)
        elif keyword == "z":
            value = xi * moire * np.reciprocal(wavelength)
        elif keyword == "moire":
            value = wavelength * z * np.reciprocal(xi)
        else:
            raise ValueError(f"Unrecognized variable of {keyword} in measurements.")
    except Exception:
        raise Exception(f"Insufficient variables to calculate {keyword}.")
    else:
        return value


def get_variable_details(keyword: str, variable_dict: dict):

    try:
        mode = variable_dict["mode"]
    except KeyError:
        raise KeyError(f"Missing mode for variable {keyword}.")

    try:
        value = variable_dict["value"]
    except KeyError:
        if mode == "calculated":
            value = None
        else:
            raise KeyError(f"Missing value for variable {keyword}.")

    try:
        units = variable_dict["units"]
    except KeyError:
        units = accepted_units[keyword]
    check_units(keyword, units)

    return mode, value, units


def gen_xi_scan(measurement_dict: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """ Returns measurement xi, moire, wavelength, and z. """

    xi_mode, xi_value, xi_units = get_variable_details("xi", measurement_dict["xi"])
    if xi_mode not in ["range", "discrete"]:
        raise ValueError("The variable mode for xi in a xi-scan measurement can be set to 'range' or 'discrete' only.")
    if xi_mode == "range":
        xi_value = range_interpreter(xi_value)
    else:
        xi_value = np.array(xi_value).astype(float)

    wavelength_mode, wavelength_value, wavelength_units = get_variable_details("wavelength",
                                                                               measurement_dict["wavelength"])
    if wavelength_mode not in ["fixed"]:
        raise ValueError("The variable mode for wavelength in a xi-scan measurement must be set to 'fixed'.")
    wavelength_value = np.ones_like(xi_value, dtype=float) * wavelength_value[0] / 10  # units of nm

    moire_mode, moire_value, moire_units = get_variable_details("moire", measurement_dict["moire"])
    z_mode, z_value, z_units = get_variable_details("z", measurement_dict["z"])
    if not (
        (moire_mode in ["fixed", "discrete"] and z_mode in ["continuous"])
        or (moire_mode in ["continuous"] and z_mode in ["fixed", "discrete"])
    ):
        raise ValueError("For a xi-scan measurement, the moire and z modes must be set as (1) moire set to either"
                         "fixed or discrete and z set to continuous or (2) moire set to continuous and z set to "
                         "fixed or discrete.")

    if z_mode == "continuous":
        z_min = np.min(z_value)
        z_max = np.max(z_value)
        z_value = []

        moire_value.sort()
        moire_set = np.copy(moire_value).astype(float)
        moire_value = []

        for x in xi_value:
            z_poss = get_missing_variable("z",
                                          xi=np.ones_like(moire_set, dtype=float)*x,
                                          wavelength=np.ones_like(moire_set, dtype=float)*wavelength_value[0],
                                          moire=moire_set)
            z_poss = np.array(z_poss)
            z_sel = np.where((z_poss <= z_max) & (z_poss >= z_min))[0]
            if len(z_sel) == 0:
                z_value.append(None)
                moire_value.append(None)
            else:
                z_sel = z_sel[-1]  # maximize period and accept z far away
                z_value.append(z_poss[z_sel])
                moire_value.append(moire_set[z_sel])

    else:
        moire_min = np.min(moire_value)
        moire_max = np.max(moire_value)
        moire_value = []

        z_value.sort()
        z_set = np.copy(z_value).astype(float)
        z_value = []

        for x in xi_value:
            moire_poss = get_missing_variable("moire",
                                              xi=np.ones_like(z_set, dtype=float)*x,
                                              wavelength=np.ones_like(z_set, dtype=float)*wavelength_value[0],
                                              z=z_set)
            moire_poss = np.array(moire_poss)
            moire_sel = np.where((moire_poss <= moire_max) & (moire_poss >= moire_min))[0]
            if len(moire_sel) == 0:
                z_value.append(None)
                moire_value.append(None)
            else:
                moire_sel = moire_sel[-1]  # maximize period and z far away
                moire_value.append(moire_poss[moire_sel])
                z_value.append(z_set[moire_sel])

    mask = np.where(z_value)

    return (xi_value.astype(float)[mask], np.array(moire_value).astype(float)[mask],
            wavelength_value.astype(float)[mask], np.array(z_value).astype(float)[mask])


def gen_wavelength_scan(measurement_dict: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """ Returns measurement xi, moire, wavelength, and z. """

    wavelength_mode, wavelength_value, wavelength_units = get_variable_details("wavelength",
                                                                               measurement_dict["wavelength"])
    if wavelength_mode not in ["range", "discrete"]:
        raise ValueError("The wavelength variable for a wavelength-scan measurement can be set to 'range' or "
                         "'discrete' only.")
    if wavelength_mode == "range":
        wavelength_value = range_interpreter(wavelength_value) / 10  # units of nm
    else:
        wavelength_value = np.array(wavelength_value).astype(float) / 10  # units of nm

    z_mode, z_value, z_units = get_variable_details("z", measurement_dict["z"])
    if z_mode != "fixed":
        raise ValueError("The z variable for a wavelength-scan measurement must be set to 'fixed'.")
    else:
        z_value = np.ones_like(wavelength_value, dtype=float)*z_value[0]

    moire_mode, moire_value, moire_units = get_variable_details("moire", measurement_dict["moire"])
    if moire_mode != "fixed":
        raise ValueError("The moire variable for a wavelength-scan measurement must be set to 'fixed'.")
    else:
        moire_value = np.ones_like(wavelength_value, dtype=float)*moire_value[0]

    xi_mode, xi_value, xi_units = get_variable_details("xi", measurement_dict["xi"])
    if xi_mode != "calculated":
        raise ValueError("The variable mode for xi in a wavelength-scan measurement can be set to 'calculated'.")
    else:
        xi_value = get_missing_variable("xi", wavelength=wavelength_value, moire=moire_value, z=z_value)

    return (xi_value.reshape(-1).astype(float), moire_value.reshape(-1).astype(float),
            wavelength_value.reshape(-1).astype(float), z_value.reshape(-1).astype(float))


def gen_z_scan(measurement_dict: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """ Returns measurement xi, moire, wavelength, and z. """

    z_mode, z_value, z_units = get_variable_details("z", measurement_dict["z"])
    if z_mode not in ["range", "discrete"]:
        raise ValueError("The z variable for a z-scan measurement can be set to 'range' or 'discrete' only.")
    if z_mode == "range":
        z_value = range_interpreter(z_value)
    else:
        z_value = np.array(z_value).astype(float)

    wavelength_mode, wavelength_value, wavelength_units = get_variable_details("wavelength",
                                                                               measurement_dict["wavelength"])
    if wavelength_mode != "fixed":
        raise ValueError("The wavelength variable for a z-scan measurement must be set to 'fixed'.")
    else:
        wavelength_value = np.ones_like(z_value, dtype=float) * wavelength_value[0] / 10  # units of nm

    moire_mode, moire_value, moire_units = get_variable_details("moire", measurement_dict["moire"])
    if moire_mode != "fixed":
        raise ValueError("The moire variable for a z-scan measurement must be set to 'fixed'.")
    else:
        moire_value = np.ones_like(z_value, dtype=float) * moire_value[0]

    xi_mode, xi_value, xi_units = get_variable_details("xi", measurement_dict["xi"])
    if xi_mode != "calculated":
        raise ValueError("The variable mode for xi in a z-scan measurement can be set to 'calculated'.")
    else:
        xi_value = get_missing_variable("xi", wavelength=wavelength_value, moire=moire_value, z=z_value)

    return (xi_value.reshape(-1).astype(float), moire_value.reshape(-1).astype(float),
            wavelength_value.reshape(-1).astype(float), z_value.reshape(-1).astype(float))


def gen_moire_scan(measurement_dict: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """ Returns measurement xi, moire, wavelength, and z. """

    moire_mode, moire_value, moire_units = get_variable_details("moire", measurement_dict["moire"])
    if moire_mode not in ["range", "discrete"]:
        raise ValueError("The moire variable for a moire-scan measurement can be set to 'range' or 'discrete' only.")
    if moire_mode == "range":
        moire_value = range_interpreter(moire_value)
    else:
        moire_value = np.array(moire_value).astype(float)

    wavelength_mode, wavelength_value, wavelength_units = get_variable_details("wavelength",
                                                                               measurement_dict["wavelength"])
    if wavelength_mode != "fixed":
        raise ValueError("The wavelength variable for a moire-scan measurement must be set to 'fixed'.")
    else:
        wavelength_value = np.ones_like(moire_value, dtype=float) * wavelength_value[0] / 10  # units of nm

    z_mode, z_value, z_units = get_variable_details("z", measurement_dict["z"])
    if z_mode != "fixed":
        raise ValueError("The z variable for a moire-scan measurement must be set to 'fixed'.")
    else:
        z_value = np.ones_like(moire_value, dtype=float) * z_value[0]

    xi_mode, xi_value, xi_units = get_variable_details("xi", measurement_dict["xi"])
    if xi_mode != "calculated":
        raise ValueError("The variable mode for xi in a moire-scan measurement can be set to 'calculated'.")
    else:
        xi_value = get_missing_variable("xi", wavelength=wavelength_value, moire=moire_value, z=z_value)

    return (xi_value.reshape(-1).astype(float), moire_value.reshape(-1).astype(float),
            wavelength_value.reshape(-1).astype(float), z_value.reshape(-1).astype(float))


def gen_multi_scan(measurement_dict: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """ Returns measurement xi, moire, wavelength, and z. """

    xi_mode, xi_value, xi_units = get_variable_details("xi", measurement_dict["xi"])
    if xi_mode != "calculated":
        raise ValueError("The xi variable in a multi-scan measurement must be set to 'calculated'.")

    moire_mode, moire_value, moire_units = get_variable_details("moire", measurement_dict["moire"])
    if moire_mode not in ["fixed", "discrete", "range"]:
        raise ValueError("The moire variable in a multi-scan measurement must be set to 'fixed', 'discrete', or "
                         "'range'.")
    if moire_mode == 'range':
        moire_value = range_interpreter(moire_value)
    moire_set = np.array(moire_value)

    wavelength_mode, wavelength_value, wavelength_units = get_variable_details("wavelength",
                                                                               measurement_dict["wavelength"])
    if wavelength_mode not in ["fixed", "discrete", "range"]:
        raise ValueError("The wavelength variable in a multi-scan measurement must be set to 'fixed', 'discrete', or "
                         "'range'.")
    if wavelength_mode == 'range':
        wavelength_value = range_interpreter(wavelength_value)
    wavelength_set = np.array(wavelength_value)/10  # units of nm

    z_mode, z_value, z_units = get_variable_details("z", measurement_dict["z"])
    if z_mode not in ["fixed", "discrete", "range"]:
        raise ValueError("The z variable in a multi-scan measurement must be set to 'fixed', 'discrete', or "
                         "'range'.")
    if z_mode == 'range':
        z_value = range_interpreter(z_value)
    z_set = np.array(z_value)

    xi_value = []
    moire_value = []
    wavelength_value = []
    z_value = []

    for m in moire_set:
        for w in wavelength_set:
            for z in z_set:
                x = get_missing_variable("xi", wavelength=w, z=z, moire=m)[0]
                xi_value.append(x)
                moire_value.append(m)
                wavelength_value.append(w)
                z_value.append(z)

    return (np.array(xi_value).astype(float), np.array(moire_value).astype(float),
            np.array(wavelength_value).astype(float), np.array(z_value).astype(float))


def gen_custom_scan(measurement_dict: dict, config_path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """ Returns measurement xi, moire, wavelength, and z. """

    xi_mode, xi_value, xi_units = get_variable_details("xi", measurement_dict["xi"])
    if xi_mode != "calculated":
        raise ValueError("Variable xi for custom-scan measurement should be set to 'calculated'.")

    moire_mode, moire_value, moire_units = get_variable_details("moire", measurement_dict["moire"])
    if moire_mode != "file":
        raise ValueError("Variable moire for custom-scan measurement should be set to 'file'.")
    else:
        moire_value = np.loadtxt(config_path.parent/moire_value).astype(float)

    wavelength_mode, wavelength_value, wavelength_units = get_variable_details("wavelength",
                                                                               measurement_dict["wavelength"])
    if wavelength_mode != "file":
        raise ValueError("Variable wavelength for custom-scan measurement should be set to 'file'.")
    else:
        wavelength_value = np.loadtxt(config_path.parent/wavelength_value).astype(float) / 10  # units of nm

    z_mode, z_value, z_units = get_variable_details("z", measurement_dict["z"])
    if z_mode != "file":
        raise ValueError("Variable z for custom-scan measurement should be set to 'file'.")
    else:
        z_value = np.loadtxt(config_path.parent/z_value).astype(float)

    check_lengths([moire_value, wavelength_value, z_value])

    xi_value = get_missing_variable("xi", moire=moire_value, wavelength=wavelength_value, z=z_value)

    return xi_value.reshape(-1), moire_value.reshape(-1), wavelength_value.reshape(-1), z_value.reshape(-1)


def gen_measurements(measurement_list, config_path):
    """Updates the class attributes that define xi, Moiré period, wavelength, and z for N images."""

    sets = []
    for measurement in measurement_list:
        try:
            measurement_mode = measurement["measurement_mode"]
        except KeyError:
            raise KeyError("Missing measurement mode. Accepted measurement modes include: 'xi-scan'"
                           ", 'z-scan', 'wavelength-scan', 'moire-scan', 'multi-scan', and 'custom-scan'.")

        if not {"xi", "moire", "z", "wavelength"} <= measurement.keys():
            raise KeyError("Insufficient variables to determine measurements. Modes for 'xi', 'wavelength',"
                           "'moire', and 'z' should all be defined for each measurement mode in measurements.")

        if measurement_mode == "xi-scan":
            points = gen_xi_scan(measurement)

        elif measurement_mode == "z-scan":
            points = gen_z_scan(measurement)

        elif measurement_mode == "wavelength-scan":
            points = gen_wavelength_scan(measurement)

        elif measurement_mode == "moire-scan":
            points = gen_moire_scan(measurement)

        elif measurement_mode == "multi-scan":
            points = gen_multi_scan(measurement)

        elif measurement_mode == "custom-scan":
            points = gen_custom_scan(measurement, config_path)

        else:
            raise ValueError(f"The measurement_mode {measurement_mode} is unaccepted. Accepted modes include: "
                             f"'xi-scan', 'z_scan', 'wavelength-scan', 'moire-scan', 'multi-scan', and "
                             f"'custom-scan'.")

        # Verify the individual scans create a consistent number of measurement points
        n = len(points[0])
        assert all(len(v) == n for v in points[1:])
        sets.append(points)

    points = [np.concatenate(v) for v in zip(*sets)]
    return points


class SimMeasurements(SimConfig):
    """
        The SimMeasurements class inherits the SimConfig class and generates the autocorrelation length (xi), Moire
        period (moire), wavelength, and sample to detector distance (z) for each measurement point in the simulation
        experiment.

        Attributes
        ----------
        measurements_xi : ndarray, length N
            - autocorrelation lengths for N image acquisitions or measurements of the simulation
            - units : nm
        measurements_moire : ndarray, length N
            - Moiré period at the detector for N image acquisitions or measurements of the simulation
            - units : mm
        measurements_wavelength : ndarray, length N
            - neutron wavelength for N image acquisitions or measurements of the simulation
            - units : nm
        measurements_z : ndarray, length N
            - sample to detector distance for N image acquisitions or measurements of the simulation
            - units : mm
    """

    measurements_xi: np.ndarray = None
    measurements_moire: np.ndarray = None
    measurements_wavelength: np.ndarray = None
    measurements_z: np.ndarray = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        points = gen_measurements(self.config["measurements"], self.config_path)

        # TODO: Do we really want to sort these?
        # In experiment files the scan points would appear in the order that they were measured.
        order = np.argsort(points[0])
        self.measurements_xi = points[0][order]
        self.measurements_moire = points[1][order]
        self.measurements_wavelength = points[2][order]
        self.measurements_z = points[3][order]
