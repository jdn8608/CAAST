from qtpy.QtWidgets import QGridLayout, QComboBox, QWidget, QLabel


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
