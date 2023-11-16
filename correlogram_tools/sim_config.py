from pathlib import Path
from typing import Any
from collections.abc import Iterator

import json


# R 2022-05-09 PAK: Simplified method.
def deep_key(obj: Any, target: str) -> Iterator:
    """
    Yield all values for a keyword found in multiple locations in a json object.

    This will search all dictionaries in the object, even if they are embedded in a list or another dictionary.
    For example::

        In  : tuple(deep_key({key: 1, extra: [{key: 2}, {notkey: 3}]}, "key"))
        Out : (1, 2)


    Note that it does descend into a key, so {key: {key: 1}} will yield
    [{key: 1}, 1] instead of [1] or [{key: 1}].

    Parameters
    ----------
    obj: dict|list
        JSON object to search.
    target: str
        The key to search for sub-dictionaries
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == target:
                yield value
            yield from deep_key(value, target)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            yield from deep_key(value, target)


class SimConfig:
    """
    The SimConfig class is an interpreter for the simulation experiment configuration defined in a .js file that has
    been converted to a dictionary. It includes information about the simulated INFER measurement points and the model
    or structure in each region of interest (ROI) of the image mask.

    Attributes
    ----------
    config : dict
        Dictionary representation of the configuration defined in the experiment configuration (.js) file.
    config_path : str, filepath
        Absolute filepath to the experiment configuration (.js) file that defines the ROIs and their structures and the
        experimental conditions.
    """
    config: dict[str, Any]
    config_path: Path

    def __init__(self, config_path: str | Path, config_dict: dict | None = None):
        # Note: Path.resolve and Path.absolute differ in handling symlinks.
        # resolve.parent is the directory containing the original file
        # while absolute.parent is the directory containing the link.
        # Since we want paths relative to link rather than the original we
        # use absolute() rather than relative() to form the full file name.
        if config_path is not None:
            config_path = Path(config_path).expanduser().absolute()
        # If config is not supplied then read it from the config file.
        if config_dict is None:
            # switching input files to json format only rather than allowing both json and relaxed json (.js)
            # config_dict = relaxed_json_load(config_path)
            with open(config_path) as file_load:
                config_dict = json.load(file_load)
                file_load.close()
            if "experiment" in config_dict:
                config_dict = config_dict["experiment"]
        self.config = config_dict
        self.config_path = config_path

    def __getitem__(self, keyword: str) -> tuple:
        """
        Enables config[keyword] and returns a list of values from the config json object for all occurrences of keyword.

        Parameters
        ----------
        keyword : str
            The deep key to search for in the config json object.
        """
        # TODO: drop deep key functionality and return config.__getitem__
        return tuple(deep_key(self.config, keyword))

    @property
    def title(self) -> str:
        """Returns the simulation experiment title."""
        return self.config["title"]

    @property
    def description(self) -> str:
        """Returns the simulation experiment description."""
        return self.config["description"]

    @property
    def mask_path(self) -> Path:
        """Returns the absolute filepath to the image mask with defined ROIs."""
        return self.config_path.parent / self.config["mask_path"]

    @property
    def thickness_path(self) -> Path:
        """Returns the absolute filepath to the image mask with defined thickness (cm)."""
        return self.config_path.parent / self.config["thickness_path"]
