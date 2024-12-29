from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox, QPushButton, QWidget, QLabel
from widgets.read_write_outputs import save_labels


def create_save_button(button_text,
                       output_filepath,
                       labels_layer=None,
                       instrument_views=None,
                       dataset_name=None,
                       scene_labels_dict=None,
                       review_csv_filepath=None,
                       review_dropdown=None,
                       review_grader=None,
                       notes_textbox=None,
                       width=None):
    """Creates and returns a submit button that is conencted to certain save options based
    on pass-in parameters.
    """
    # Create the Save & Submit Button
    save_button = QPushButton(button_text)
    if width:
        save_button.setFixedWidth(width)
    # Connect the button's click event to a call to save_labels()
    save_button.clicked.connect(
        lambda: save_labels(output_filepath=output_filepath,
                            labels=labels_layer,
                            dataset_name=dataset_name,
                            views=instrument_views,
                            scene_labels_dict=scene_labels_dict,
                            review_filepath=review_csv_filepath,
                            review_dropdown=review_dropdown,
                            review_grader=review_grader,
                            notes_textbox=notes_textbox))
    return save_button


def create_scene_dropdowns(scene_labels, priors=None):
    """Creates a grid of dropdown boxes for scene label options provided

    Args:
        scene_labels: a list of scene attributes to (binary) label if present within the scene
        priors: if not None, corresponding fill-in values from prior labeling for each of the entries in scene_labels

    Returns:
        a dictionary of the scene_labels and their corrsponding values
        the QGridLayout for the dropdown widgets

    """
    scene_labels_dict = dict((q, QComboBox()) for q in scene_labels)

    grid_layout = QGridLayout()
    grid_layout.setContentsMargins(0, 0, 0,
                                   0)  # Remove margins around the grid layout
    grid_layout.setSpacing(10)

    # Add label and dropdown for each scene-level labels in the grid layout
    max_columns = 4
    row = 0
    col = 0

    # Add label and dropdown for each scene-level label
    for i, (label_text, combo_box) in enumerate(scene_labels_dict.items()):
        combo_box.addItems(["Unclear", "Yes", "No"])
        if priors:
            combo_box.setCurrentText(priors[i])  # Set "Unclear" as default
        else:
            combo_box.setCurrentText("Unclear")  # Set "Unclear" as default
        combo_box.setFixedWidth(200)

        label_widget = QLabel(label_text.replace("_", " ").capitalize())
        grid_layout.addWidget(label_widget, row, col)
        grid_layout.addWidget(combo_box, row, col + 1)

        col += 2
        if col >= max_columns * 2:  # Move to the next row after 4 pairs
            col = 0
            row += 1

    return scene_labels_dict, grid_layout
