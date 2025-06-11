"""
This modeule is used to create the visual tool to open and view remote sensing imager data.
This tool can be opened in review-mode, or pixel-labeling mode, changing the functuonality
and widgets loaded into the tool.
"""
import json
import os
import sys

import numpy as np

import napari
from qtpy.QtCore import Qt, QPoint
from qtpy.QtGui import QFont
from qtpy.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QTabWidget, QScrollArea, QLabel,
                            QTextEdit, QComboBox, QSizePolicy, QFrame,
                            QPushButton, QSplitter, QMenu)

from util.LayerType import LayerType
from util.colormaps import get_all_colormaps

from widgets.Sliders import create_sliders
from widgets.LayerManager import LayerManager
from widgets.PointOfViewNavigator import PointOfViewNavigator
from widgets.SubmitButtons import create_save_button
from widgets.SceneLabelGrid import create_scene_dropdowns
from widgets.GradeSlider import GradeSlider
from widgets.ThresholdPanel import ThresholdWidget
from widgets.LogicGatesPanel import LogicGatesWidget


def add_layers(data_layer_dict,
               manager,
               shape,
               viewer,
               config,
               load_labels_name='',
               label_mode=True):
    """Add imaage and label layers to the napari viewer, and providing connectors
    for down-stream widgets based on the LayerType attributes.

    Args:
        data_layer_dict : a dictionary where keys are the name of the layers, and
                        the values are tuples -> value [0] is a LayerType and value
                        [1] is a NumPy array of the data.
        manager         : a LayerManager widget to organize layers that are added
                        based on namking for LayerType.
        shape           : shape of the image type layers to visualize
        viewer          : the napari viewer
        config          : vis config dictionary to get visualization options like
                        colormaps etc.
        load_labels_name: the name of the layer to add as intial labels set by the
                        user.

    Returns:
        3 tuples:
            tuple[0] -> the editing data and layer
            tuple[1] -> a NumPy array and a list of layers for image data 
            tuple[2] -> a list of label NumPy arrays and a list of label layers
    """
    shape = (shape[3], shape[0], shape[1], shape[2])

    (band_colormap, label_colormap, mask_colormap, nan_colormap,
     surf_colormap) = get_all_colormaps(config)

    if not label_mode:
        editing_data = None
        editing_layer = None
        edit_data_override = True
    # check if load_labels is defined, if not, set to 0
    elif load_labels_name is None or load_labels_name == '':
        load_labels_name = '0'

    # Check if the fill value is an int, if now, set-up for checking if layer to be
    # filled by a instrument layer
    try:
        editing_data = np.zeros(
            (shape[0], shape[1], shape[2]), dtype=int) + int(load_labels_name)
        edit_data_override = True
    except:
        editing_data = None
        editing_layer = None
        # If there is a load labels name provided (not None), then search for it
        if load_labels_name:
            edit_data_override = False
        # Otherwise, there is no editing labels to load (in review mode)
        else:
            edit_data_override = True

    # Empty list for all image type layers
    # Initial size of the shape provided from data ingestion (spectral dim)
    im_layers = [None] * shape[3]
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
        layer_type, data_temp = data_layer_dict[layer_name]

        if layer_type is LayerType.SHAPE:
            current_layer = viewer.add_shapes(
                data_temp,
                shape_type="polygon",
                face_color="transparent",
                edge_width=5,
                edge_color="red",
                opacity=0.5,  # 50% transparency
                name=layer_name)
            manager.add_layer_to_group(layer_type.value, current_layer)
        elif layer_type is LayerType.RGB:
            print(data_temp.shape)
            data_temp = np.transpose(data_temp, (3, 0, 1, 2))
            current_layer = viewer.add_image(data_temp,
                                             name=layer_name,
                                             rgb=True)
            # Add the layer to the correct group in the layer manager
            manager.add_layer_to_group(layer_type.value, current_layer)

        else:
            data = np.transpose(data_temp, (2, 0, 1))
            print(data.shape)

            # If regular image layer, add a layer with a gray-scale colormap
            if layer_type in (LayerType.GRAY_BAND, LayerType.VIEW_GEO,
                              LayerType.LAT_LON):

                current_layer = viewer.add_image(data[...],
                                                 name=layer_name,
                                                 colormap=band_colormap)
                # Add the layer to the correct group in the layer manager
                manager.add_layer_to_group(layer_type.value, current_layer)

                im_layers[im_iter] = current_layer
                im_data[..., im_iter] = data
                im_iter += 1

            # DTT layers will have additional functionality later on
            elif layer_type is LayerType.DTT:
                current_layer = viewer.add_image(data[...],
                                                 name=layer_name,
                                                 colormap=band_colormap)
                # Add the layer to the correct group in the layer manager
                manager.add_layer_to_group(layer_type.value, current_layer)

                im_layers[im_iter] = current_layer
                im_data[..., im_iter] = data
                im_iter += 1
            # OBSERVABLE layers will have additional functionality later on
            elif layer_type is LayerType.OBSERVABLE:
                current_layer = viewer.add_image(data[...],
                                                 name=layer_name,
                                                 colormap=band_colormap)
                # Add the layer to the correct group in the layer manager
                manager.add_layer_to_group(layer_type.value, current_layer)

                im_layers[im_iter] = current_layer
                im_data[..., im_iter] = data
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
                elif layer_type is LayerType.SURFACE_ID:
                    current_colormap = surf_colormap

                if current_colormap is not None:
                    # Add labels layer to viewer
                    current_layer = viewer.add_labels(
                        data[...], name=layer_name, colormap=current_colormap)
                    current_layer.editable = False  # do not allow for editing

                    # Add the layer to the correct group in the layer manager
                    manager.add_layer_to_group(layer_type.value, current_layer)

                    # Append the layer and np data arrays to the corresponding lists
                    label_layers.append(current_layer)
                    label_list.append(data)

                    # Check to see if current layer is initial editing labels set by user
                    if (not edit_data_override) and \
                        (layer_name.upper() == load_labels_name.upper()):
                        editing_data = data.copy()

    # Check to see if editing data was found... if not, store as zeros
    if label_mode and editing_data is None and load_labels_name:
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
    if label_mode and load_labels_name:
        editing_layer = viewer.add_labels(editing_data[...],
                                          name='Editing',
                                          colormap=label_colormap)
        # Add the layer to the correct group in the layer manager
        manager.add_layer_to_group(LayerType.MANUAL_LABELS.value,
                                   editing_layer)

        label_layers.append(editing_layer)
        label_list.append(editing_data)

    return (editing_data, editing_layer), (im_data, im_layers), \
        (label_list, label_layers)


def get_notes_tab(output_filepath, prior_notes=None):
    """Create and return a note taking widget for the bottom of the user to
    be allowed to take notes of the scene they are viewing, in both review or
    editing/labeling modes

    Args:
        output_filepath : the filepath to write output files to (as a formatted string)
        prior_notes : a string representing past notes taken by user(s) to pre-load the notes
            widget with. If not provided, then no prior text will be loaded.
    """
    notes_tab_widget = QWidget()
    notes_layout = QVBoxLayout()
    # Create the TextEdit Widget to let users type in
    notes_widget = QTextEdit()
    # If there are no prior notes, put placeholder text
    if prior_notes is None:
        notes_widget.setPlaceholderText("Write your notes here...")
    # Otherwise, fill with prior notes text
    else:
        notes_widget.setPlainText(prior_notes)
    # Add Notes save button
    save_button = create_save_button(button_text="Save Notes",
                                     output_filepath=output_filepath,
                                     notes_textbox=notes_widget)
    # Add to the widget layout/object
    notes_layout.addWidget(notes_widget)
    notes_layout.addWidget(save_button)
    notes_tab_widget.setLayout(notes_layout)

    # Return the tab to be added to the tabs widget
    return notes_tab_widget


def get_scene_label_tab(output_filepath, scene_labels):
    """Creates and returns a new tab to the bottom tab area for labeling whether
    specific attributes are present within the scene. This is done by adding
    a grid of drowndrop widgets for each attribute.

    Args:
        output_filepath : the filepath to write output files to (as a formatted string)
        scene_labels : a list of types of attributes to add (setting default values), or a
            dictionary of keys of attributes, within initial values as dict values

    Returns:
        the scene labels tab widget

    Exception:
        if scene_labels is not a list or dict, throw an exception to the user and hault.
    """
    # Create the Scene Labels Tab widget and layout
    scene_labels_widget = QWidget()
    scene_labels_layout = QVBoxLayout()

    # Check if the scene_labels are a list or dict and create the dropdowns accordingly
    if isinstance(scene_labels, list):
        scene_labels_dict, scene_labels_grid_layout = create_scene_dropdowns(
            scene_labels)
    elif isinstance(scene_labels, dict):
        scene_labels_dict, scene_labels_grid_layout = create_scene_dropdowns(
            list(scene_labels.keys()), priors=list(scene_labels.values()))
    else:
        raise Exception(
            "Scene Attributes/Labels provided from file reader is of invalid type.\n"
            "The scene_attribute variable should be a list attributes or dict with "
            "keys as the attributes and values as prior labels/initial values set.\n"
            "See README for more detials")

    # Add the scene labels to the layout
    scene_labels_layout.addLayout(scene_labels_grid_layout)

    # Create and connect a buttom to save out the contents of the dropdowns
    scene_labels_save_button = create_save_button(
        button_text="Save Scene Labels",
        output_filepath=output_filepath,
        scene_labels_dict=scene_labels_dict)
    # Add the save button to the layout
    scene_labels_layout.addWidget(scene_labels_save_button)

    # Set the tab widget to the create layout
    scene_labels_widget.setLayout(scene_labels_layout)

    # Return the scene labels tab widget
    return scene_labels_widget


def get_pixellabel_tool_tab(output_filepath,
                            data_pointer,
                            views,
                            dataset_name,
                            controls=None):
    """Create and return the pixel labeling/editing tool tab.

    Args:
        output_filepath : the filepath to write output files to (as a formatted string).
        data_pointer : pointer to the editing data NumPy array.
        views : the name of the views for this instrument.
        dataset_name : the dataset_name for saving out the file..
        controls : optional parameter to provide the dock layer controls to move them
            from the left side of the screen to this tab.
    """
    # Create and Set-up the editing tab widget and layout
    editing_widget = QWidget()
    main_layout = QVBoxLayout()
    sub_layout = QHBoxLayout()

    # Create and connect the save pixel labels buttons
    label_save_button = create_save_button(button_text="Save Pixel Labels",
                                           output_filepath=output_filepath,
                                           labels_layer=data_pointer,
                                           instrument_views=views,
                                           dataset_name=dataset_name)
    # Add the button to the tab
    main_layout.addWidget(label_save_button)

    # if the dock layer controls are provided, add them to this tab
    if controls is not None:
        # Add controls to the lower portion of the tab
        sub_layout.addWidget(controls)

    # Add the sub to the main
    main_layout.addLayout(sub_layout)
    # Set the tab layout to the main
    editing_widget.setLayout(main_layout)

    # return the editing tab widget
    return editing_widget


def get_review_mode_tab(output_filepath,
                        csv_filepath,
                        review_data=None,
                        min_val=1,
                        max_val=5,
                        controls=None):
    """Create and return the review mode tab if we are in review mode. This tab will have an approve
    or reject dropdown menu, a 'Grade Slider', and a save/submit buttom to record the values of these
    sub-wigdets. The dropdown menu allows a user to approve or reject labels (cloud mask) for a
    given scene... functionally flaggin if the scene labels need to be edited later. Furthermore,
    the use can use the Grade Slider to describe the quality of the labels, where higher the value
    means the labels are excellent. Then the save button records these into a CSV file.

    Args:
        output_filepath : the filepath to write output files to (as a formatted string)
        csv_filpeath :  the filepath to the csv file to record this scene's entry
        review_data :  a tuple containing (review_grade, review_status). These sub-values are used
            to provide initial values of the Grade Slider and dropdown widgets from prior grading
            by the user.
        min_val : the minimum value for the grade slider. default value of 1.
        max_val : the maximum value for the grade slider. default value of 5.
        controls : optional parameter to provide the dock layer controls to move them
            from the left side of the screen to this tab.

    Return:
        the review mode tab widget
    """

    # Ensure that the review_data is a tuple and not none to get the sub-values
    if review_data is not None and isinstance(review_data, tuple):
        # Seperate out the review data
        review_grade, review_status = review_data
    else:
        review_grade = None
        review_status = None

    # initialize review mode tab widget area and layout
    review_tab_widget = QWidget()
    review_layout = QHBoxLayout()

    # if the dock layer controls are provided, add them to this tab
    if controls is not None:
        review_layout.addWidget(controls)

    # Create left side layout
    review_vbox = QVBoxLayout()

    # Create a dropdown box to approve or reject the current scene
    dropdown = QComboBox()
    dropdown.addItems(["Ungraded", "Approve", "Reject"])
    dropdown.setCurrentText(
        review_status if review_status is not None else "Ungraded")
    dropdown.setFixedWidth(300)

    # Create a review grade slider
    gs = GradeSlider(min_val, max_val, 1,
                     review_grade if review_grade is not None else 1)

    # Create a save button for the review mode slider/labels
    review_save_button = create_save_button(button_text="Save Review Labels",
                                            output_filepath=output_filepath,
                                            review_csv_filepath=csv_filepath,
                                            review_dropdown=dropdown,
                                            review_grader=gs)

    # Set layout of the tab
    review_vbox.addWidget(dropdown)
    review_vbox.addWidget(review_save_button)
    review_layout.addLayout(review_vbox)
    review_layout.addWidget(gs)
    review_tab_widget.setLayout(review_layout)

    # return the review tab widget
    return review_tab_widget


class AdaptiveSplitViewer(QMainWindow):

    def __init__(self, data_layer_dict, config, shape, label_mode,
                 load_labels_name):
        # call super init for a QMainWindow
        super().__init__()

        # Set image shape param for dimensionality references
        self.image_shape = shape

        # Set window name and aspect geometry
        self.setWindowTitle("Napari Multi-Viewer")
        self.setGeometry(100, 100, 1600, 800)

        # Create parent/main layout
        self.main_widget = QWidget()
        self.outer_layout = QVBoxLayout()
        self.main_widget.setLayout(self.outer_layout)
        self.setCentralWidget(self.main_widget)

        # Create QSplitter horizontal layout for additional viewers
        self.viewer_row_layout = QHBoxLayout()
        self.viewer_splitter = QSplitter(Qt.Horizontal)
        self.viewer_row_layout.addWidget(self.viewer_splitter)
        self.outer_layout.addLayout(self.viewer_row_layout)

        # Assign Main Viewer and turn off default dock widgets
        self.main_viewer = napari.Viewer()
        self.viewers = [self.main_viewer]
        self.main_viewer.window.qt_viewer.dockLayerList.setVisible(
            False)  # Override the Dock Layer list
        self.main_viewer.window.qt_viewer.dockLayerControls.setMaximumHeight(
            300)
        self.viewer_splitter.addWidget(self.main_viewer.window._qt_window)

        # Set up left tab widget for left panel tools
        left_tabs = QTabWidget()
        left_tabs.setTabPosition(QTabWidget.South)
        left_tabs.setMinimumWidth(330)
        self.main_viewer.window.add_dock_widget(left_tabs,
                                                area="left",
                                                name="Left Panel")

        # Assign reference to layer_manager and add to main viewer
        self.layer_manager = LayerManager(
            napari_viewer=self.main_viewer,
            shape=(shape[-1], shape[0], shape[1]),
            init_groups=[layer.value
                         for layer in LayerType])  # replaces layerlist
        self.layer_manager.setMinimumWidth(300)
        self.layer_manager.setMinimumHeight(350)
        self.layer_manager.setSizePolicy(QSizePolicy.Expanding,
                                         QSizePolicy.Preferred)

        # Add layer and controls to a scroll-able tab
        layers_and_controls_scroll_area = QScrollArea()
        layers_and_controls_scroll_area.setWidgetResizable(True)
        layers_and_controls_widget = QWidget()
        layers_and_controls_vlayout = QVBoxLayout(layers_and_controls_widget)
        layers_and_controls_vlayout.addWidget(
            self.main_viewer.window.qt_viewer.dockLayerControls)
        layers_and_controls_vlayout.addWidget(self.layer_manager)
        layers_and_controls_scroll_area.setWidget(layers_and_controls_widget)
        left_tabs.addTab(layers_and_controls_scroll_area,
                         "Layers and Controls")

        # Add the imagery and labels from data_layer_dict to the main viewer
        (edit_np, edit_layer), \
        (im_np, im_layers), \
        (label_list, label_layers) = add_layers(data_layer_dict,
                                               self.layer_manager,
                                               self.image_shape,
                                               self.main_viewer,
                                               config,
                                               load_labels_name=load_labels_name if label_mode else '',
                                               label_mode=label_mode)

        # Create min/max sliders for image layers
        self.min_max_slider, self.min_max_layout = create_sliders(
            option=int(config["min_max_slider_option"]),
            viewer=self.
            main_viewer,  # viewer stil needs to be passed for SelectionMinMaxSlider() dependent on viewer event changes
            layers=im_layers,
            data=im_np)
        self.layer_manager.layer_renamed.connect(
            self.update_sliders_name
        )  # Connect the renaming event call to this function
        self.min_max_layout.setMinimumWidth(300)
        self.min_max_layout.setSizePolicy(QSizePolicy.Expanding,
                                          QSizePolicy.Preferred)
        left_tabs.addTab(self.min_max_layout, "Set Bounds")

        # To be replace later within layer manager
        # Prelim widget to add layers to new or existing viewers
        controls_layout = QHBoxLayout()
        self.layer_selector = QComboBox()
        self.viewer_selector = QComboBox()
        self.add_btn = QPushButton("Add Layer to Viewer")
        self.add_btn.clicked.connect(self.add_layer_to_viewer)

        controls_layout.addWidget(QLabel("Layer:"))
        controls_layout.addWidget(self.layer_selector)
        controls_layout.addWidget(QLabel("Viewer:"))
        controls_layout.addWidget(self.viewer_selector)
        controls_layout.addWidget(self.add_btn)
        self.outer_layout.addLayout(controls_layout)

        self.update_layer_dropdown()
        self.update_viewer_selector()
        # END of replace

        # Add cursor indicators to the main viewer
        self.cursor_layers = {}
        self.add_cursor_indicator(self.main_viewer)
        self.add_border_shape(self.main_viewer, self.image_shape[1:])
        self.main_viewer.mouse_move_callbacks.append(
            self.update_cursor_positions)

        # Sync time steppers for new viewers to the main view
        self.main_viewer.dims.events.current_step.connect(self.sync_time_steps)

    def update_sliders_name(old_name, new_name):
        """Loops through alll Min/Max Sliders to check for if they have the name
        of old_name. If so, call their update_layer_name() with the new_name

        Args:
            old_name: a string representing the old name of a renamed layer
            new_name: a string representing the new name of a renamed layer
        """
        for mms in self.min_max_slider:
            if old_name == mms.name:
                mms.update_layer_name()

    def sync_time_steps(self, event):
        step = self.main_viewer.dims.current_step[0]
        for viewer in self.viewers:
            if viewer != self.main_viewer:
                viewer.dims.current_step = (
                    step, ) + viewer.dims.current_step[1:]

    def add_cursor_indicator(self, viewer):
        num_times = self.image_shape[0]
        data = [[t, 0, 0] for t in range(num_times)]
        layer = viewer.add_points(data=data,
                                  name='Cursor',
                                  ndim=3,
                                  size=12,
                                  face_color='white',
                                  border_color='red',
                                  opacity=0.6)
        viewer.scale_bar.visible = False
        self.cursor_layers[viewer] = layer

    def update_cursor_positions(self, viewer, event):
        pos = event.position
        num_times = self.image_shape[0]
        y, x = pos[1], pos[2]

        for v in self.viewers:
            cursor_layer = self.cursor_layers.get(v)
            if cursor_layer:
                if len(cursor_layer.data) < self.image_shape[0]:
                    cursor_layer.data = [[t_, 0, 0]
                                         for t_ in range(self.image_shape[0])]
                new_data = cursor_layer.data.copy()
                for t in range(num_times):
                    new_data[t] = [t, y, x]
                cursor_layer.data = new_data

    def add_border_shape(self, viewer, shape_dims):
        viewer_index = self.viewers.index(viewer)
        viewer_name = "Main Viewer" if viewer_index == 0 else f"Viewer {viewer_index+1}"

        shape = np.array([[-5, -5], [-5, shape_dims[1] + 5],
                          [shape_dims[0] + 5, shape_dims[1] + 5],
                          [shape_dims[0] + 5, -5], [-5, -5]])

        text_props = {
            'string': [viewer_name],
            'anchor': 'center',
            'translation': [-20 - (shape_dims[0] / 2), 50],
            'size': 40,
            'color': 'red',
            'scaling': True
        }

        viewer.add_shapes(data=[shape],
                          shape_type='polygon',
                          edge_color='transparent',
                          edge_width=3,
                          face_color='transparent',
                          text=text_props,
                          name="Border Rectangle")

    def update_layer_dropdown(self):
        self.layer_selector.clear()
        for layer in self.main_viewer.layers:
            if layer.name != 'Cursor':
                self.layer_selector.addItem(layer.name)

    def update_viewer_selector(self):
        self.viewer_selector.clear()
        for i in range(1, len(self.viewers)):
            self.viewer_selector.addItem(f"Viewer {i+1}")
        self.viewer_selector.addItem("+ New Viewer")

    def add_layer_to_viewer(self):
        selected_layer_name = self.layer_selector.currentText()
        selected_index = self.viewer_selector.currentIndex()

        if selected_layer_name == "":
            return

        layer = self.main_viewer.layers[selected_layer_name]

        if selected_index == self.viewer_selector.count() - 1:
            new_viewer = napari.Viewer()
            new_viewer.scale_bar.visible = False
            new_viewer.window._qt_viewer.controls.setVisible(False)
            new_viewer.window._qt_viewer.dockLayerList.setVisible(False)
            new_viewer.window._qt_viewer.dockLayerControls.setVisible(False)

            viewer_widget = new_viewer.window._qt_window

            viewer_widget.setContextMenuPolicy(Qt.CustomContextMenu)
            viewer_widget.customContextMenuRequested.connect(
                lambda pos, v=new_viewer, w=viewer_widget: self.
                viewer_context_menu(pos, v, w))

            self.viewer_splitter.addWidget(viewer_widget)
            self.viewers.append(new_viewer)

            self.sync_all_viewers()

            target_viewer = new_viewer

            if layer._type_string == 'image':
                target_viewer.add_image(layer.data, name=layer.name)
            elif layer._type_string == 'labels':
                target_viewer.add_labels(layer.data, name=layer.name)

            self.add_cursor_indicator(target_viewer)
            self.add_border_shape(target_viewer, layer.data.shape[1:])
            target_viewer.mouse_move_callbacks.append(
                self.update_cursor_positions)
            self.sync_time_steps(None)

        else:
            target_viewer = self.viewers[selected_index + 1]
            target_viewer.layers.clear()
            if layer._type_string == 'image':
                target_viewer.add_image(layer.data, name=layer.name)
            elif layer._type_string == 'labels':
                target_viewer.add_labels(layer.data, name=layer.name)

            self.add_cursor_indicator(target_viewer)
            self.add_border_shape(target_viewer, layer.data.shape[1:])
            target_viewer.mouse_move_callbacks.append(
                self.update_cursor_positions)

        self.update_viewer_selector()

    def viewer_context_menu(self, pos: QPoint, viewer, widget):
        menu = QMenu()
        close_action = menu.addAction("Close Viewer")
        action = menu.exec_(widget.mapToGlobal(pos))
        if action == close_action:
            self.remove_viewer(viewer, widget)

    def remove_viewer(self, viewer, widget):
        if viewer in self.viewers:
            self.viewers.remove(viewer)
            viewer.close()
            self.update_viewer_selector()

    def sync_all_viewers(self):
        for src_viewer in self.viewers:
            for dst_viewer in self.viewers:
                if src_viewer != dst_viewer:
                    src_viewer.camera.events.center.connect(
                        lambda e, src=src_viewer, dst=dst_viewer: self.
                        sync_camera(src, dst))
                    src_viewer.camera.events.zoom.connect(
                        lambda e, src=src_viewer, dst=dst_viewer: self.
                        sync_camera(src, dst))

    def sync_camera(self, src_viewer, dst_viewer):
        dst_viewer.camera.center = src_viewer.camera.center
        dst_viewer.camera.zoom = src_viewer.camera.zoom


def create_tool(label_mode,
                data_layer_dict,
                shape,
                output_file_info,
                views,
                angles,
                scene_attrs,
                csv_filepath,
                review_data,
                notes,
                load_labels_name='',
                config_filepath='./util/default_vizconfig.json'):
    """This script creates the tool for the user from calls to sub-functions and widgets
    and connects these accordingly from the provided data.

    Args:
        label_mode          : a bool where True-> open tool in pixel editing/labeling mode;
                            False -> open the tool in review mode.
        data_layer_dict     : a dictionary where the keys are the names of the layer, and the
                            values are tuples of the LayerType Enum and the corresponding NumPy 
                            data. This is the imagery and labels provided for visualization.
        shape               : the shape of the band imagery in data_layer_dict
        output_file_info    : a tuple where [0] is the output filepath convention, and [2]
                            is the dataset name
        views               : a list of the names of the views for the instrument data loaded
        angles              : the viewing angles for each view
        scene_attrs         : a list or dict of the scene attributes to load. If None, the 
                            scene labeling tab will not be loaded
        csv_filpeath        : the filepath the csv file to record the review mode entries from
                            the user.
        review_data         : a tuple where [0] is the review grade and [1] is the review status
                            saved last for this scene. If Nones, the user has not edited this
                            scene yet.
        notes               : loaded notes if they were previously taken for this scene by a user
        load_labels_name    : the string of the name of the layer in the keys of data_layer_dict
                            entered by the user to pre-load for editing labels
        config_filepath     : filepath to the visualization config file for various settings to
                            change how the tool works and is created.

    Returns:
        Opens the Napari software with the data pre-loaded and extra widgets to the user
    """

    output_filepath, dataset_name = output_file_info

    # Load Visualizaiton Config File
    with open(config_filepath, "r") as file:
        config = json.load(file)

    app = QApplication(sys.argv)
    viewer_app = AdaptiveSplitViewer(data_layer_dict=data_layer_dict,
                                     config=config,
                                     shape=shape,
                                     label_mode=label_mode,
                                     load_labels_name=load_labels_name)
    viewer_app.show()
    sys.exit(app.exec_())

    ## Set-up Napari Viewer as back-end
    #viewer = napari.Viewer(show=False)
    ##viewer.window._qt_window.showFullScreen()
    #viewer.show()

    ## Add Min/Max Slider for Image Layers
    #min_max_slider, min_max_layout = create_sliders(
    #    option=int(config["min_max_slider_option"]),
    #    # viewer stil needs to be passed for SelectionMinMaxSlider() dependent on viewer event changes
    #    viewer=viewer,
    #    layers=im_layers,
    #    data=im_np)
    #viewer.window.add_dock_widget(min_max_layout,
    #                              name="Min-Max Range Slider",
    #                              area='right')

    ## Create a function to search for a layer to rename from LayerManager event
    #def update_sliders_name(old_name, new_name):
    #    """Loops through alll Min/Max Sliders to check for if they have the name
    #    of old_name. If so, call their update_layer_name() with the new_name

    #    Args:
    #        old_name: a string representing the old name of a renamed layer
    #        new_name: a string representing the new name of a renamed layer
    #    """
    #    for mms in min_max_slider:
    #        if old_name == mms.name:
    #            mms.update_layer_name()

    ## Connect the renaming event call to this function
    #layer_manager.layer_renamed.connect(update_sliders_name)

    ## If there are multiple view-angles found, add a POV Slider to navigate them
    #if im_np.shape[-1] > 1:

    #    # Access the slider widget
    #    qt_dims = viewer.window._qt_viewer.dims
    #    # Grab the first slider widget
    #    slider_widget = qt_dims.slider_widgets[0]

    #    # Create a formatted string and label to present
    #    # the camera and VZA strings to the user
    #    view_indicator_string = "Camera: {0} ; VZA: {1}"
    #    view_indicator_label = QLabel(
    #        view_indicator_string.format(views[slider_widget.slider.value()],
    #                                     angles[slider_widget.slider.value()]))

    #    # Add a new QLabel to replace the numeric text
    #    slider_widget.layout().insertWidget(0, view_indicator_label)

    #    # Define a callback function to update the label dynamically
    #    def update_view_label(view_dim):
    #        """Update the custom text next to the view dim slider

    #        Args:
    #            view_dim: integer representing the index of the view we
    #                      are currently presenting in the view panel from
    #                      the slider.
    #        """
    #        if 0 <= view_dim < len(views):  # Ensure within bounds
    #            view_indicator_label.setText(
    #                view_indicator_string.format(views[view_dim],
    #                                             angles[view_dim]))

    #    # Connect the slider's valueChanged signal to the callback
    #    slider_widget.slider.valueChanged.connect(update_view_label)

    #    # Configure the slider default settings
    #    slider_widget.axis = 0
    #    slider_widget.fps = 2
    #    slider_widget.loop_mode = "back_and_forth"

    ##    # Create Tab widget & layout
    ##    POV_tab_widget = QWidget()
    ##    POV_tab_layout = QVBoxLayout()
    ##    POV_tab_widget.setLayout(POV_tab_layout)
    ##    # create title for top of POV nav widget
    ##    POV_title = QLabel("Point of View Navigator",
    ##                       alignment=Qt.AlignCenter,
    ##                       font=QFont("Arial", weight=QFont.Bold))
    ##    POV_tab_layout.addWidget(POV_title)

    ##    #top_layout.addWidget(POV_title)  # add to top layout

    ##    # Create the POV nav to iterate through view angles
    ##    POV_nav = PointOfViewNavigator(im_layers=im_layers,
    ##                                   min_max_slider=min_max_slider,
    ##                                   im_data=im_np,
    ##                                   label_layers=label_layers,
    ##                                   label_data=label_list,
    ##                                   view_text=views,
    ##                                   angles=angles)
    ##    # Connect viewer's key events to this widget
    ##    # left arrow -> goes to next left view
    ##    # right arrow -> goes to next right view
    ##    viewer.bind_key('Left', POV_nav.go_left)
    ##    viewer.bind_key('Right', POV_nav.go_right)
    ##    #top_layout.addWidget(POV_nav)  # add POV nav to the top widget area
    ##    POV_tab_layout.addWidget(POV_nav)
    ##    bottom_tabs.addTab(POV_tab_widget, "Point of View Navigator")

    ## Create and add the Notes Tab to the bottom tab area
    #bottom_tabs.addTab(get_notes_tab(output_filepath, prior_notes=notes),
    #                   "Notes")

    ## Create Scene Labeling Dropdown Tab
    #if scene_attrs:
    #    bottom_tabs.addTab(get_scene_label_tab(output_filepath, scene_attrs),
    #                       "Scene Labeling")

    ## Get the dock layer controls from the napari window
    ## NOTE: this will be depreciated in napari 0.6.0
    ## TODO: Open up an issue on GitHub and update for future napari versions
    #dock_layer_controls = viewer.window.qt_viewer.dockLayerControls
    #dock_layer_controls.setMaximumHeight(300)
    ## Create a scroll area for the dock layer controls and add it to this widget
    ##layer_controls_scroll_area = QScrollArea()
    ##layer_controls_scroll_area.setMaximumWidth(300)
    ##layer_controls_scroll_area.setWidgetResizable(True)
    ##layer_controls_scroll_area.setWidget(dock_layer_controls)
    #layer_controls_scroll_area = None

    ## If Label/Editing Mode, load the Labeling Tool tab
    #if label_mode:
    #    bottom_tabs.addTab(
    #        get_pixellabel_tool_tab(output_filepath,
    #                                edit_np,
    #                                views,
    #                                dataset_name,
    #                                controls=layer_controls_scroll_area),
    #        "Pixel Tools")

    #    # Create and add a tab for the ThresholdWidget
    #    threshold_gate_widget = QWidget()
    #    threshold_gate_layout = QHBoxLayout()
    #    # Remove extra spacing and margins from the layout
    #    threshold_gate_layout.setSpacing(0)
    #    threshold_gate_layout.setContentsMargins(0, 0, 0, 0)
    #    # Create the ThresholdWidget and LogicGatesWidget
    #    thresh_widget = ThresholdWidget(viewer, layer_manager, views=views)
    #    logic_gate_widget = LogicGatesWidget(viewer, layer_manager)
    #    # Set size policies to allow both widgets to share space equally
    #    thresh_widget.setSizePolicy(QSizePolicy.Expanding,
    #                                QSizePolicy.Preferred)
    #    logic_gate_widget.setSizePolicy(QSizePolicy.Expanding,
    #                                    QSizePolicy.Preferred)
    #    # Create a vertical line
    #    vertical_line = QFrame()
    #    vertical_line.setFrameShape(QFrame.VLine)
    #    vertical_line.setFrameShadow(QFrame.Sunken)
    #    vertical_line.setLineWidth(
    #        10)  # Set the width of the line for visibility
    #    vertical_line.setStyleSheet("background-color: #414851;")

    #    # Add widgets to the layout
    #    threshold_gate_layout.addWidget(
    #        thresh_widget, stretch=1)  # Assign equal stretch factor
    #    threshold_gate_layout.addWidget(vertical_line)  # Add vertical line
    #    threshold_gate_layout.addWidget(logic_gate_widget, stretch=1)
    #    # Set the layout for the container widget
    #    threshold_gate_widget.setLayout(threshold_gate_layout)
    #    # Add the tab to the bottom_tabs
    #    bottom_tabs.addTab(threshold_gate_widget, "Thresholding & Logic Gates")

    ## Otherwise, load the Review Mode tab
    #else:
    #    if isinstance(config["grade_slider_min"], int) and \
    #    isinstance(config["grade_slider_max"],int) and \
    #    config["grade_slider_min"] < config["grade_slider_max"]:
    #        bottom_tabs.addTab(
    #            get_review_mode_tab(output_filepath,
    #                                csv_filepath,
    #                                review_data=review_data,
    #                                min_val=config["grade_slider_min"],
    #                                max_val=config["grade_slider_max"],
    #                                controls=layer_controls_scroll_area),
    #            "Review Grading")
    #    else:
    #        bottom_tabs.addTab(
    #            get_review_mode_tab(output_filepath,
    #                                csv_filepath,
    #                                review_data=review_data,
    #                                controls=layer_controls_scroll_area), \
    #            "Review Grading")

    #bottom_tabs.setMaximumHeight(200)

    ## Open the viewer window to the user
    #napari.run()
