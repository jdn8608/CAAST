import json
import os
import numpy as np
import napari

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox, QPushButton, QWidget, QLabel

from colorama import Fore, Style

from widgets.colormaps import get_all_colormaps
from widgets.SubmitButtons import create_label_save_buttons, create_review_save_buttons, create_scene_dropdowns
from widgets.read_write_outputs import read_labels
from widgets.create_sliders import create_sliders
from widgets.LegendWidget import create_legend
from widgets.PointOfViewNavigator import PointOfViewNavigator


def visualize(data,
              band_names,
              output_filepath,
              label_mode=False,
              prior_mask=False,
              prior_manual_labels=False,
              load_labels=None,
              dataset_name=None,
              vis_config_file='./util_files/default_vizconfig.json',
              views='AN',
              angles='0.0'):

    viewer = napari.Viewer(show=False)
    #viewer.window._qt_window.showFullScreen()
    viewer.show()

    with open(vis_config_file, "r") as file:
        config = json.load(file)
    scene_labels = config['scene_labels']

    band_colormaps, label_colormap, mask_colormap = get_all_colormaps(config)
    label_colormap_text = {
        int(key): value
        for key, value in config["label_string_text"].items()
    }

    legend_widget, legend_width, legend_height = create_legend(
        label_colormap, label_colormap_text)
    viewer.window.add_dock_widget(legend_widget,
                                  area=config["legend_location"],
                                  name="Legend")
    # if legend on left, move the default dock controls/tools down
    if config["legend_location"] == 'left':
        layer_list_dock = viewer.window._qt_viewer.dockLayerList
        layer_controls_dock = viewer.window._qt_viewer.dockLayerControls
        layer_controls_dock.setMaximumWidth(legend_width)
        layer_controls_dock.setMaximumHeight(400)
        layer_list_dock.setMaximumWidth(legend_width)
        viewer.window.add_dock_widget(layer_controls_dock, area='left')
        viewer.window.add_dock_widget(layer_list_dock, area='left')

    # set up lists for widgets
    name_end = None
    label_layers = []
    label_data = []

    # load prior mask (cloud mask) into a (non-edit) layer
    if not prior_mask is None:
        name_end = -1
        orig_labels_layer = viewer.add_labels(prior_mask[:, :, 0].astype(int),
                                              name=band_names[name_end],
                                              colormap=mask_colormap)
        orig_labels_layer.editable = False
        label_layers.append(orig_labels_layer)
        label_data.append(prior_mask[:, :, :].astype(int))

    # add data to visualize
    im_layers = viewer.add_image(data[:, :, :, 0],
                                 name=band_names[:name_end],
                                 channel_axis=2,
                                 colormap=band_colormaps)

    # load the prior manual labels into a (non-edit) layer
    if prior_manual_labels:
        try:
            man_labels, man_scene_attrs = read_labels(output_filepath,
                                                      dataset_name,
                                                      views,
                                                      scene_attrs=scene_labels)
            man_labels_layer = viewer.add_labels(man_labels[:, :,
                                                            0].astype(int),
                                                 name="Prior Manual Labels",
                                                 colormap=label_colormap)
            man_labels_layer.editable = False
            label_layers.append(man_labels_layer)
            label_data.append(man_labels.astype(int))

        except FileNotFoundError as error:
            print(Fore.RED + f"Error encountered: {error}")
            print(Fore.YELLOW +
                  "Prior labels file was not found (see error above)")
            print("Fore-going loading prior labels")
            print(Style.RESET_ALL)
            prior_manual_labels = False

    if label_mode:
        # load editing layer
        if load_labels is None:
            edit_data = 1 + np.zeros(data[:, :, 0, :].shape, dtype=int)
        elif not prior_mask is None and load_labels.upper() == "MASK":
            edit_data = prior_mask[:, :, :].astype(int)
        elif prior_manual_labels and load_labels.upper() == "MANUAL":
            edit_data = man_labels.astype(int)
            if scene_labels:
                scene_labels = man_scene_attrs
        else:
            raise Warning(
                "load_labels settigs have ambigous settings when compare to prior_mask or prior_manual_labels variables\n defaulting to 'None' value functionality and loading zeros as the Editing Layer"
            )
            edit_data = np.zeros(data[:, :, 0, :].shape, dtype=int)

        edit_layer = viewer.add_labels(edit_data[:, :, 0],
                                       name='Editing',
                                       colormap=label_colormap)
        label_layers.append(edit_layer)
        label_data.append(edit_data)

    min_max_slider, min_max_layout = create_sliders(
        option=int(config["min_max_slider_option"]),
        # viewer stil needs to be passed for SelectionMinMaxSlider() dependent on viewer event changes
        viewer=viewer,
        layers=im_layers,
        data=data,
        band_names=band_names[:name_end])

    viewer.window.add_dock_widget(min_max_layout,
                                  name="Min-Max Range Slider",
                                  area=config["slider_location"])

    if data.shape[-1] > 1:
        POV_nav = PointOfViewNavigator(im_layers=im_layers,
                                       min_max_slider=min_max_slider,
                                       im_data=data,
                                       label_layers=label_layers,
                                       label_data=label_data,
                                       view_text=views,
                                       angles=angles)

        # Connect viewer's key events to this widget
        viewer.bind_key('Left', POV_nav.go_left)
        viewer.bind_key('Right', POV_nav.go_right)
        viewer.window.add_dock_widget(POV_nav,
                                      name="Point of View Navigator",
                                      area='top')

    # rename  later
    # Create a save button widget
    save_button_widget = QWidget()
    save_button_layout = QVBoxLayout()
    if scene_labels:
        if isinstance(scene_labels, list):
            scene_labels_dict, grid_layout = create_scene_dropdowns(
                scene_labels)
        else:
            scene_labels_dict, grid_layout = create_scene_dropdowns(
                list(scene_labels.keys()), priors=list(scene_labels.values()))
        save_button_layout.addLayout(grid_layout)
    else:
        scene_labels_dict = {}

    if label_mode:
        save_button = create_label_save_buttons(
            labels_layer=POV_nav if data.shape[-1] > 1 else edit_layer,
            output_filepath=output_filepath,
            instrument_views=views,
            dataset_name=dataset_name,
            scene_labels_dict=scene_labels_dict)

        # add the editing label savebutton
    else:
        save_button = create_review_save_buttons(
            output_filepath=output_filepath,
            scene_labels_dict=scene_labels_dict)

    save_button_layout.addWidget(save_button)
    # Add the button widget to Napari's dock
    save_button_widget.setLayout(save_button_layout)
    viewer.window.add_dock_widget(save_button_widget,
                                  area=config["button_location"])

    napari.run()
