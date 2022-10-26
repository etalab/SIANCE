import json

# Configuration stored, not to be accessed
# from outside this file
__CONFIG = None


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
            with open("config.json", "r") as f:
                __CONFIG = json.load(f)
        except FileNotFoundError:
            with open("../config.json", "r") as f:
                __CONFIG = json.load(f)

    return __CONFIG
