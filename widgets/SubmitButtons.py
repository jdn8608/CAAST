from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox, QPushButton, QWidget, QLabel
from widgets.read_write_outputs import save_labels


def create_label_save_buttons(
    labels_layer,
    output_filepath,
    instrument_views,
    dataset_name=None,
    scene_labels_dict=None,
):

    # Create the Save & Submit Button
    save_button = QPushButton('Save Labels')
    save_button.clicked.connect(lambda: save_labels(
        labels_layer.data,
        output_filepath,
        dataset_name,
        instrument_views,
        scene_labels_dict,
    ))
    return save_button


def create_scene_dropdowns(scene_labels, priors=None):
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
