import json
import os

import numpy as np

import napari
from qtpy.QtCore import Qt
from qtpy.QtGui import QFont
from qtpy.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QTextEdit, QComboBox

from file_readers.LayerType import LayerType
from widgets.colormaps import get_all_colormaps
from widgets.create_sliders import create_sliders
from widgets.PointOfViewNavigator import PointOfViewNavigator
from widgets.SubmitButtons import create_save_button, create_scene_dropdowns
from widgets.GradeSlider import GradeSlider


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
        editing_layer = None
        # If there is a load labels name provided (not None), then search for it
        if load_labels_name:
            edit_data_override = False
        # Otherwise, there is no editing labels to load (in review mode)
        else:
            edit_data_override = True

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
                editing_data = data.copy()

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


def get_pixellabel_tool_tab(output_filepath, data_pointer, views,
                            dataset_name):
    """Create and return the pixel labeling/editing tool tab.

    Args:
        output_filepath : the filepath to write output files to (as a formatted string).
        data_pointer : pointer to the editing data NumPy array.
        views : the name of the views for this instrument.
        dataset_name : the dataset_name for saving out the file..
    """
    # Create and Set-up the editing tab widget and layout
    editing_widget = QWidget()
    editing_layout = QVBoxLayout()
    # Create and connect the save pixel labels buttons
    label_save_button = create_save_button(button_text="Save Pixel Labels",
                                           output_filepath=output_filepath,
                                           labels_layer=data_pointer,
                                           instrument_views=views,
                                           dataset_name=dataset_name)
    # Add the button to the tab
    editing_layout.addWidget(label_save_button)
    editing_widget.setLayout(editing_layout)

    # return the editing tab widget
    return editing_widget


def get_review_mode_tab(output_filepath,
                        csv_filepath,
                        review_data=None,
                        min_val=1,
                        max_val=5):
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

    # Create left side layout
    left_review_vbox = QVBoxLayout()

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
    left_review_vbox.addWidget(dropdown)
    left_review_vbox.addWidget(review_save_button)
    review_layout.addLayout(left_review_vbox)
    review_layout.addWidget(gs)
    review_tab_widget.setLayout(review_layout)

    # return the review tab widget
    return review_tab_widget


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
                config_filepath='./util_files/default_vizconfig.json'):

    output_filepath, dataset_name = output_file_info

    # Load Visualizaiton Config File
    with open(config_filepath, "r") as file:
        config = json.load(file)

    # Set-up Napari Viewer as back-end
    viewer = napari.Viewer(show=False)
    #viewer.window._qt_window.showFullScreen()
    viewer.show()

    # Create Area layouts for tool widgets
    # Create top area and add to viewer
    top_widget = QWidget()
    top_layout = QVBoxLayout()
    top_widget.setLayout(top_layout)
    viewer.window.add_dock_widget(
        top_widget,
        #name="Point of View Navigator",
        area="top")
    # Create bottom area for tabs and add to viewer
    bottom_tabs = QTabWidget()
    bottom_tabs.setTabPosition(QTabWidget.North)
    viewer.window.add_dock_widget(bottom_tabs, area="bottom")

    # Add the instrument layer data to the viewer
    (edit_np, edit_layer), \
        (im_np, im_layers), \
        (label_list, label_layers) = add_layers(data_layer_dict,
                                               shape,
                                               viewer,
                                               config,
                                               load_labels_name=load_labels_name if label_mode else '')

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

    # If there are multiple view-angles found, add a POV Slider to navigate them
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

    # Create and add the Notes Tab to the bottom tab area
    bottom_tabs.addTab(get_notes_tab(output_filepath, prior_notes=notes),
                       "Notes")

    # Create Scene Labeling Dropdown Tab
    if scene_attrs:
        bottom_tabs.addTab(get_scene_label_tab(output_filepath, scene_attrs),
                           "Scene Labeling")

    # If Label/Editing Mode, load the Labeling Tool tab
    if label_mode:
        bottom_tabs.addTab(
            get_pixellabel_tool_tab(output_filepath, edit_np, views,
                                    dataset_name), "Pixel Tools")
    # Otherwise, load the Review Mode tab
    else:
        if isinstance(config["grade_slider_min"], int) and \
        isinstance(config["grade_slider_max"],int) and \
        config["grade_slider_min"] < config["grade_slider_max"]:
            bottom_tabs.addTab(
                get_review_mode_tab(output_filepath,
                                    csv_filepath,
                                    review_data=review_data,
                                    min_val=config["grade_slider_min"],
                                    max_val=config["grade_slider_max"]),
                "Review Grading")
        else:
            bottom_tabs.addTab(
                get_review_mode_tab(output_filepath,
                                    csv_filepath,
                                    review_data=review_data), \
                "Review Grading")

    # Open the viewer window to the user
    napari.run()
