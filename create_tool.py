import json
import os

import numpy as np
import napari
from qtpy.QtCore import Qt
from qtpy.QtGui import QFont
from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel

from file_readers.LayerType import LayerType
from widgets.colormaps import get_all_colormaps
from widgets.create_sliders import create_sliders
from widgets.PointOfViewNavigator import PointOfViewNavigator


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

    # Empty list for all image type layers
    # Initial size of the shape provided from data ingestion (spectral dim)
    im_layers = [None] * shape[2]
    # Image data NumPy array
    im_data = np.zeros(shape)
    im_iter = 0

    # Create an empty lists for the points to the label layer objects
    label_layers = []
    # Create an empty list for the pointers to the label data
    # the entries are the np arrays
    label_list = []

    # Loop through all layers by their name and add them to the viewer with the correct
    # widget formatting/connections for other widgets
    for layer_name in data_layer_dict.keys():
        layer_type, data = data_layer_dict[layer_name]

        # If Gray band, add a layer with a gray-scale colormap
        if layer_type is LayerType.GRAY_BAND:
            current_layer = viewer.add_image(data[..., 0],
                                             name=layer_name,
                                             colormap=band_colormap)
            im_layers[im_iter] = current_layer
            im_data[..., im_iter, :] = data
            im_iter += 1

        # If not an image-type layer, process as labels
        else:
            data = data.astype(int)
            # Determine which color map to use for labels
            if layer_type is LayerType.CLOUD_MASK:
                current_colormap = mask_colormap
            elif layer_type is LayerType.MANUAL_LABELS:
                current_colormap = label_colormap
            elif layer_type is LayerType.NAN_MASK:
                current_colormap = nan_colormap

            # Add labels layer to viewer
            current_layer = viewer.add_labels(data[..., 0],
                                              name=layer_name,
                                              colormap=current_colormap)
            current_layer.editable = False  # do not allow for editing

            # Append the layer and np data arrays to the corresponding lists
            label_layers.append(current_layer)
            label_list.append(data)

            # Check to see if current layer is initial editing labels set by user
            if (not edit_data_override) and \
                (layer_name.upper() == load_labels_name.upper()):
                editing_data = data

    # Check to see if editing data was found... if not, store as zeros
    if editing_data is None and load_labels_name:
        # ambigous name was provided (not found)
        warnings.warn(
            "load_labels settings string was not found in the naming convetions"
            " for the layers loaded. \nPlease refine the string entered you would "
            "like initial labels loaded for editing.\nTo view the naming conventions"
            " of the loaded layers, turn verbose on. \n "
            "Loading zeros into the Editing Layer for now.",
            category=UserWarning)
        edit_data = np.zeros(data.shape, dtype=int)

    # Add editing_data as an editing layer to the viewer
    if load_labels_name:
        editing_layer = viewer.add_labels(editing_data[..., 0],
                                          name='Editing',
                                          colormap=label_colormap)
        label_layers.append(editing_layer)
        label_list.append(editing_data)

    return (editing_data, editing_layer), (im_data, im_layers), \
        (label_list, label_layers)


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

    #Create Area layouts for tool widgets
    top_widget = QWidget()
    top_layout = QVBoxLayout()
    top_widget.setLayout(top_layout)
    viewer.window.add_dock_widget(
        top_widget,
        #name="Point of View Navigator",
        area="top")


    # Add the instrument layer data to the viewer
    (edit_np, edit_layer), \
        (im_np, im_layers), (label_list, label_layers) = add_layers(data_layer_dict,
               shape,
               viewer,
               config,
               load_labels_name=load_labels_name)

    # Add Min/Max Slider for Image Layers
    min_max_slider, min_max_layout = create_sliders(
        option=int(config["min_max_slider_option"]),
        # viewer stil needs to be passed for SelectionMinMaxSlider() dependent on viewer event changes
        viewer=viewer,
        layers=im_layers,
        data=im_np)
    viewer.window.add_dock_widget(min_max_layout,
                                  name="Min-Max Range Slider",
                                  area='right')

    if im_np.shape[-1] > 1:
        # create title for top of POV nav widget
        POV_title = QLabel("Point of View Navigator",
                           alignment=Qt.AlignCenter,
                           font=QFont("Arial", weight=QFont.Bold))
        top_layout.addWidget(POV_title)  # add to top layout
        # Create the POV nav to iterate through view angles
        POV_nav = PointOfViewNavigator(im_layers=im_layers,
                                       min_max_slider=min_max_slider,
                                       im_data=im_np,
                                       label_layers=label_layers,
                                       label_data=label_list,
                                       view_text=views,
                                       angles=angles)
        # Connect viewer's key events to this widget
        # left arrow -> goes to next left view
        # right arrow -> goes to next right view
        viewer.bind_key('Left', POV_nav.go_left)
        viewer.bind_key('Right', POV_nav.go_right)
        top_layout.addWidget(POV_nav)  # add POV nav to the top widget area

    # Open the viewer window to the user
    napari.run()
