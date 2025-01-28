"""
This module is used to create a ThresholdWidget to apply a threshold operation to an image layer, 
resulting in a new labels layer.
"""

import numpy as np

import napari
from qtpy.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QCheckBox, QLineEdit, QPushButton, QLabel

from util.LayerType import LayerType


class ThresholdWidget(QWidget):

    def __init__(self, viewer, layer_manager):
        super().__init__()
        self.viewer = viewer
        self.layer_manager = layer_manager

        # Create default N/A text for when label layers are selected
        self.default_text = "Please select a layer..."
        self.threshold_counter = 0  # Counter to track the number of thresholds created

        # Set up main layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Horizontal layout for layer, operation, and value
        self.horizontal_layout = QHBoxLayout()

        # Dropdown to select image layer
        self.layer_dropdown = QComboBox()
        self.horizontal_layout.addWidget(self.layer_dropdown)

        # Dropdown to select operation
        self.operation_dropdown = QComboBox()
        self.operation_dropdown.addItems([">", "<", "<=", ">=", "==", "!="])
        self.horizontal_layout.addWidget(self.operation_dropdown)

        # Input field for threshold value
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Threshold Value")
        self.horizontal_layout.addWidget(self.value_input)

        # Editable checkbox and descriptive label
        self.editable_checkbox = QCheckBox(
            "Enable editing of the new labels layer")
        self.editable_checkbox.setChecked(False)  # Default: not editable
        self.horizontal_layout.addWidget(self.editable_checkbox)

        # Add horizontal layout to main layout
        self.layout.addLayout(self.horizontal_layout)

        # Button to create thresholded labels layer
        self.create_button = QPushButton("Create")
        self.layout.addWidget(self.create_button)

        # Connect signals
        self.create_button.clicked.connect(self.create_threshold_layer)

        # Populate the layer dropdown whenever the viewer layers change
        self.viewer.layers.events.inserted.connect(self.update_layer_list)
        self.viewer.layers.events.removed.connect(self.update_layer_list)
        self.viewer.layers.selection.events.active.connect(
            self.update_layer_from_selection)
        self.update_layer_list()

    def update_layer_list(self, event=None):
        """Update the layer dropdown with image layers from the viewer."""
        current_selection = self.layer_dropdown.currentText()
        print(current_selection)
        self.layer_dropdown.clear()
        self.layer_dropdown.addItems([self.default_text])
        image_layers = [
            layer.name for layer in self.viewer.layers
            if isinstance(layer, napari.layers.Image)
        ]
        self.layer_dropdown.addItems(image_layers)
        if current_selection in image_layers:
            self.layer_dropdown.setCurrentText(current_selection)

    def update_layer_from_selection(self, event=None):
        """Update the dropdown to reflect the currently selected layer in the viewer."""
        active_layer = self.viewer.layers.selection.active
        if active_layer:
            if isinstance(active_layer, napari.layers.Image):
                index = self.layer_dropdown.findText(active_layer.name)
                if index != -1:
                    self.layer_dropdown.setCurrentIndex(index)
            elif isinstance(active_layer, napari.layers.Labels):
                self.layer_dropdown.setCurrentText(self.default_text)
                print(
                    "Selected a labels layer. Threshold operation is not applicable."
                )

    def create_threshold_layer(self):
        """Create a labels layer based on the threshold operation."""
        # Get selected image layer
        selected_layer_name = self.layer_dropdown.currentText()
        if not selected_layer_name or selected_layer_name == self.default_text:
            print("No valid image layer selected.")
            return

        image_layer = self.viewer.layers[selected_layer_name]
        if not isinstance(image_layer, napari.layers.Image):
            print("Selected layer is not an image layer.")
            return

        # Get selected operation
        operation = self.operation_dropdown.currentText()

        # Get threshold value
        try:
            threshold_value = float(self.value_input.text())
        except ValueError:
            print("Invalid threshold value. Please enter a numeric value.")
            return

        # Perform threshold operation
        image_data = image_layer.data

        operation_map = {
            ">": np.greater,
            "<": np.less,
            "<=": np.less_equal,
            ">=": np.greater_equal,
            "==": np.equal,
            "!=": np.not_equal
        }
        threshold_func = operation_map[operation]
        labels_data = threshold_func(image_data, threshold_value).astype(int)

        # Generate layer name ignoring the prefix for duplication check
        base_name = f"{selected_layer_name} {operation} {threshold_value}"
        existing_names = [
            layer.name.split(': ', 1)[-1] for layer in self.viewer.layers
        ]

        if base_name in existing_names:
            print(
                f"Layer '{base_name}' already exists. Not adding a new layer.")
            return

        # Add prefix for display name
        self.threshold_counter += 1
        new_layer_name = f"Th{self.threshold_counter}: {base_name}"

        # Add the new labels layer
        im_temp = self.viewer.add_labels(labels_data, name=new_layer_name)
        im_temp.editable = self.editable_checkbox.isChecked()
        self.layer_manager.add_layer_to_group(LayerType.THRESHOLDS.value,
                                              im_temp)

        print(f"Added labels layer: {new_layer_name}")
