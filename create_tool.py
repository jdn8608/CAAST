import json
import os

from file_readers.LayerType import LayerType
from widgets.colormaps import get_all_colormaps

import numpy as np
import napari


def add_layers(data_layer_dict, shape, viewer, config, load_labels_name=''):
    band_colormap, label_colormap, mask_colormap, nan_colormap = get_all_colormaps(
        config)


    # Check if the fill value is an int, if now, set-up for checking if layer to be
    # filled by a instrument layer
    try:
        edit_data = np.zeros(data.shape, dtype=int) + int(load_labels_name)
        edit_data_override = True 
    except:
        editing_data = None
        edit_data_override = False

    for layer_name in data_layer_dict.keys():
        layer_type, data = data_layer_dict[layer_name]

        # If Gray band, add a layer with a gray-scale colormap
        if layer_type is LayerType.GRAY_BAND:
            viewer.add_image(data[..., 0],
                             name=layer_name,
                             colormap=band_colormap)

        # If not an image-type layer, process as labels
        else:
            # Determine which color map to use for labels
            if layer_type is LayerType.CLOUD_MASK:
                current_colormap = mask_colormap
            elif layer_type is LayerType.MANUAL_LABELS:
                current_colormap = label_colormap
            elif layer_type is LayerType.NAN_MASK:
                current_colormap = nan_colormap

            # Add labels layer to viewer
            current_layer = viewer.add_labels(data[..., 0].astype(int),
                                              name=layer_name,
                                              colormap=current_colormap)
            current_layer.editable = False  # do not allow for editing

            # Check to see if current layer is initial editing labels set by user
            if not edit_data_override and layer_name.upper() == load_labels_name.upper():
                editing_data = data.astype(int)

    # Check to see if editing data was found... if not, store as zeros
    elif editing_data is None and load_labels_name:
        # ambigous name was provided (not found)
        warnings.warn(
            "load_labels settings string was not found in the naming convetions"
            "for the layers loaded. \nPlease refine the string entered you would "
            "like initial labels loaded for editing.\nTo view the naming conventions"
            " of the loaded layers, turn verbose on. \n "
            "Loading zeros into the Editing Layer for now.",
            category=UserWarning)
        edit_data = np.zeros(data.shape, dtype=int)

    if load_labels_name:
        editing_layer = viewer.add_labels(editing_data[..., 0],
                                          name='Editing',
                                          colormap=label_colormap)

    return editing_data


def create_tool(data_layer_dict,
                shape,
                output_filepath,
                views,
                angles,
                scene_attrs,
                review_data,
                load_labels_name='',
                config_filepath='./util_files/default_vizconfig.json'):

    # Load Visualizaiton Config File
    with open(config_filepath, "r") as file:
        config = json.load(file)

    # Set-up Napari Viewer as back-end
    viewer = napari.Viewer(show=False)
    #viewer.window._qt_window.showFullScreen()
    viewer.show()

    add_layers(data_layer_dict,
               shape,
               viewer,
               config,
               load_labels_name=load_labels_name)

    napari.run()
