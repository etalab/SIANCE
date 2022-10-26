import json
import os

# Configuration path stored, not to be accessed
# from outside this file

__CONFIG = None
__CONFIG_PATH = "config.json"


def set_config_file(path):
    """
    Force the config path (useful to run several versions in parallel)
    """
    global __CONFIG
    with open(path, "r") as f:
        __CONFIG = json.load(f)


def get_config():
    """
    Retrieve the configuration object
    of this module, reading from
    the file `config.json`
    whenever __CONFIG is None
    """
    global __CONFIG
    if __CONFIG is None:
        try:
            with open(__CONFIG_PATH, "r") as f:
                __CONFIG = json.load(f)
        except FileNotFoundError:
            with open(os.path.join("..", "..", __CONFIG_PATH), "r") as f:
                __CONFIG = json.load(f)
    return __CONFIG
