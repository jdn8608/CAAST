import json


def _get_custom_colormap(options, plural=False):
    with open('./util_files/custom_colormaps.json', "r") as file:
        custom_colormaps = json.load(file)
    return {
        int(key): [float(item) for item in values]
        for key, values in custom_colormaps[options].items()
    }


def get_colormap(option):
    colormap = option
    if colormap[0:7] == 'custom_':
        colormap = _get_custom_colormap(colormap[7:])
    return colormap


def get_colormaps_from_config(config, option_name):
    if isinstance(config[option_name], str):
        return get_colormap(config[option_name])
    elif isinstance(config[option_name], list):
        return [get_colormap(opt) for opt in config[option_name]]
    elif config[option_name] is None:
        return None
    else:
        raise Exception(
            "Erro within visualization config file: 'f{option_name}' option is of invalid type 'f{type(config['band_color_maps'])}'"
        )


def get_all_colormaps(config):
    return tuple([
        get_colormaps_from_config(config, x)
        for x in ['band_colormaps', 'label_colormap', 'mask_colormap']
    ])
