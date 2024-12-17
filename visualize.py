import json
import os
import numpy as np
import napari

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox, QPushButton, QWidget, QLabel, QTabWidget, QTextEdit, QFileDialog
from qtpy.QtGui import QFont

from widgets.colormaps import get_all_colormaps
from widgets.SubmitButtons import create_save_button, create_scene_dropdowns, GradeSlider
from widgets.read_write_outputs import read_labels
from widgets.create_sliders import create_sliders
from widgets.LegendWidget import create_legend
from widgets.PointOfViewNavigator import PointOfViewNavigator


def visualize(data,
              band_names,
              output_filepath,
              review_mode_csv_filepath='./labels/cloud_mask_review.csv',
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

    bottom_tabs = QTabWidget()
    bottom_tabs.setTabPosition(QTabWidget.North)

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
        man_labels, man_scene_attrs, review_grade, review_status = read_labels(
            output_filepath, dataset_name, views, scene_attrs=scene_labels)
        if man_labels is not None:
            man_labels_layer = viewer.add_labels(man_labels[:, :,
                                                            0].astype(int),
                                                 name="Prior Manual Labels",
                                                 colormap=label_colormap)
            man_labels_layer.editable = False
            label_layers.append(man_labels_layer)
            label_data.append(man_labels.astype(int))

        prior_manual_labels = False
    else:
        man_scene_attrs = None
        review_grade = None
        review_status = None

    if scene_labels and man_scene_attrs:
        scene_labels = man_scene_attrs

    if label_mode:
        # load editing layer
        if load_labels is None:
            edit_data = 1 + np.zeros(data[:, :, 0, :].shape, dtype=int)
        elif not prior_mask is None and load_labels.upper() == "MASK":
            edit_data = prior_mask[:, :, :].astype(int)
        elif prior_manual_labels and load_labels.upper() == "MANUAL":
            edit_data = man_labels.astype(int)
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

    top_widget = QWidget()
    top_layout = QVBoxLayout()
    if data.shape[-1] > 1:
        POV_title = QLabel("Point of View Navigator",
                           alignment=Qt.AlignCenter,
                           font=QFont("Arial", weight=QFont.Bold))
        top_layout.addWidget(POV_title)
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
        top_layout.addWidget(POV_nav)

    # Tab Set-up:
    #TODO: add back in customization .json settings?? maybe not
    # Editing Tab:
    if label_mode:
        editing_widget = QWidget()
        editing_layout = QVBoxLayout()
        label_save_button = create_save_button(
            button_text="Save Pixel Labels",
            output_filepath=output_filepath,
            labels_layer=POV_nav.data
            if data.shape[-1] > 1 else edit_layer.data,
            instrument_views=views,
            dataset_name=dataset_name)
        editing_layout.addWidget(label_save_button)
        editing_widget.setLayout(editing_layout)
        bottom_tabs.addTab(editing_widget, "Editing")
    else:
        review_tab_widget = QWidget()
        review_layout = QHBoxLayout()

        left_review_vbox = QVBoxLayout()
        dropdown = QComboBox()
        dropdown.addItems(["Ungraded", "Approve", "Reject"])
        dropdown.setCurrentText(
            review_status if review_status is not None else "Ungraded")
        dropdown.setFixedWidth(300)
        left_review_vbox.addWidget(dropdown)

        gs = GradeSlider(1, 5, 1,
                         review_grade if review_grade is not None else 1)

        review_save_button = create_save_button(
            button_text="Save Review Labels",
            output_filepath=output_filepath,
            review_csv_filepath=review_mode_csv_filepath,
            review_dropdown=dropdown,
            review_grader=gs)
        left_review_vbox.addWidget(review_save_button)
        review_layout.addLayout(left_review_vbox)

        review_layout.addWidget(gs)

        review_tab_widget.setLayout(review_layout)
        bottom_tabs.addTab(review_tab_widget, "Review")

    # Notes Tab
    notes_tab_widget = QWidget()
    notes_layout = QVBoxLayout()
    notes_widget = QTextEdit()
    notes_widget.setPlaceholderText("Write your notes here...")
    notes_layout.addWidget(notes_widget)
    notes_save_button = create_save_button(button_text="Save Notes",
                                           output_filepath=output_filepath,
                                           notes_textbox=notes_widget)
    notes_layout.addWidget(notes_save_button)
    notes_tab_widget.setLayout(notes_layout)
    bottom_tabs.addTab(notes_tab_widget, "Notes")

    # Scene Labels Tab
    if scene_labels:
        scenelabels_widget = QWidget()
        scenelabels_layout = QVBoxLayout()
        if isinstance(scene_labels, list):
            scene_labels_dict, scenelabels_grid_layout = create_scene_dropdowns(
                scene_labels)
        else:
            scene_labels_dict, scenelabels_grid_layout = create_scene_dropdowns(
                list(scene_labels.keys()), priors=list(scene_labels.values()))
        scenelabels_layout.addLayout(scenelabels_grid_layout)
        scenelabels_save_button = create_save_button(
            button_text="Save Scene Labels",
            output_filepath=output_filepath,
            scene_labels_dict=scene_labels_dict)
        scenelabels_layout.addWidget(scenelabels_save_button)
        scenelabels_widget.setLayout(scenelabels_layout)
        bottom_tabs.addTab(scenelabels_widget, "Scene Labels")

    else:
        scene_labels_dict = {}

    save_all_button = create_save_button(
        button_text="Save All",
        output_filepath=output_filepath,
        labels_layer=None if not label_mode else
        POV_nav.data if data.shape[-1] > 1 else edit_layer.data,
        instrument_views=views,
        dataset_name=dataset_name,
        scene_labels_dict=scene_labels_dict,
        review_csv_filepath=review_mode_csv_filepath,
        review_dropdown=None if label_mode else dropdown,
        review_grader=None if label_mode else gs)

    top_layout.addWidget(save_all_button)
    top_widget.setLayout(top_layout)
    viewer.window.add_dock_widget(
        top_widget,
        #name="Point of View Navigator",
        area="top")

    viewer.window.add_dock_widget(bottom_tabs, area="bottom")

    napari.run()
