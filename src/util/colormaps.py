"""
This module is used to read/format colormaps chosen by the user for visualization by napari software
"""
import json


def list_custom_colormap_names():
    """Return the available custom colormap names prefixed with ``custom_``."""
    with open('./settings/custom_colormaps.json', 'r') as file:
        data = json.load(file)
    return [f"custom_{name}" for name in data.keys()]


def list_all_colormap_names():
    """Return napari built-in colormaps plus any custom ones."""
    from napari.utils.colormaps import AVAILABLE_COLORMAPS

    return list(AVAILABLE_COLORMAPS.keys()) + list_custom_colormap_names()


def _get_custom_colormap(option, plural=False):
    """opens custom colormaps file, retrieves the specified custom colormap based on it's name, 
    and returns the colormap as a dictionary

   Args:
        option: the name of the custom colormap

    Returns:
        a dictionary of the custom colormap
    """
    with open('./settings/custom_colormaps.json', "r") as file:
        custom_colormaps = json.load(file)
    return {
        int(key): [float(item) for item in values]
        for key, values in custom_colormaps[option].items()
    }


def get_colormap(option):
    """gets the colormap option, and checks if the chosen colormap is a custom one; 
    If so, calls the custom colormap function

   Args:
        option:  the name of the colormap

    Return:
        the colormap name
    """
    colormap = option
    if colormap[0:7] == 'custom_':
        colormap = _get_custom_colormap(colormap[7:])
    return colormap


def get_colormaps_from_config(config, option_name):
    """Gets the colormaps for a specific use from the config file and name of the colormap

    Args:
        config: the config options for colormaps (dictionary)
        option_name: the key for a use case for a colormap to retrieve from the configs 

    Returns:
        the colormap formatted as a dictionary
    """
    if isinstance(config[option_name], str):
        return get_colormap(config[option_name])
    elif isinstance(config[option_name], list):
        return [get_colormap(opt) for opt in config[option_name]]
    elif config[option_name] is None:
        return None
    else:
        raise Exception(
            "Error within visualization config file: 'f{option_name}' option is of invalid type 'f{type(config['band_color_maps'])}'"
        )


def get_all_colormaps(config):
    """gets the colormaps for all needed config styles 

    Args:
        config: the config options from the config file 

    Returns:
        colormaps for each colormap use-case
    """
    return tuple([
        get_colormaps_from_config(config, x) for x in [
            'band_colormap', 'label_colormap', 'mask_colormap', 'nan_colormap',
            'surf_colormap'
        ]
    ])
