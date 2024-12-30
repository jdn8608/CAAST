import json
import os

from file_readers.LayerType import LayerType

import numpy as np
import napari


def add_layers(data_layer_dict, shape, viewer):
    for layer_name in data_layer_dict.keys():
        layer_type, data = data_layer_dict[layer_name]

        if layer_type is LayerType.GRAY_BAND:
            viewer.add_image(data[..., 0], name=layer_name)


def create_tool(data_layer_dict, shape, output_filepath, views, angles,
                scene_attrs, review_data):

    # Set-up Napari Viewer as back-end
    viewer = napari.Viewer(show=False)
    #viewer.window._qt_window.showFullScreen()
    viewer.show()

    add_layers(data_layer_dict, shape, viewer)

    napari.run()
