"""
This module is used to create a widget to allow users to combine label layers with logic gates
"""
import numpy as np

import napari
from qtpy.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QCheckBox, QLineEdit, QPushButton, QLabel

from util.LayerType import LayerType


class LogicGatesWidget(QWidget):

    def __init__(self, viewer, layer_manager):
        super().__init__()
        self.viewer = viewer
        self.layer_manager = layer_manager

        # Set up main layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Horizontal layout for selecting layers and operation
        self.horizontal_layout = QHBoxLayout()

        # Dropdown to select first labels layer
        self.layer1_dropdown = QComboBox()
        self.horizontal_layout.addWidget(self.layer1_dropdown)

        # Dropdown to select operation
        self.operation_dropdown = QComboBox()
        self.operation_dropdown.addItems(["AND", "OR", "NAND", "NOR", "XOR"])
        self.horizontal_layout.addWidget(self.operation_dropdown)

        # Dropdown to select second labels layer
        self.layer2_dropdown = QComboBox()
        self.horizontal_layout.addWidget(self.layer2_dropdown)

        # Editable checkbox and descriptive label
        self.editable_checkbox = QCheckBox(
            "Enable editing of the new labels layer")
        self.editable_checkbox.setChecked(False)  # Default: not editable
        self.horizontal_layout.addWidget(self.editable_checkbox)

        # Add horizontal layout to main layout
        self.layout.addLayout(self.horizontal_layout)

        # Button to combine labels layers
        self.combine_button = QPushButton("Combine")
        self.layout.addWidget(self.combine_button)

        # Connect signals
        self.combine_button.clicked.connect(self.combine_labels_layers)

        # Populate the layer dropdowns whenever the viewer layers change
        self.viewer.layers.events.inserted.connect(self.update_layer_list)
        self.viewer.layers.events.removed.connect(self.update_layer_list)
        self.update_layer_list()

    def update_layer_list(self, event=None):
        """Update the layer dropdowns with labels layers from the viewer."""
        current_selection1 = self.layer1_dropdown.currentText()
        current_selection2 = self.layer2_dropdown.currentText()
        self.layer1_dropdown.clear()
        self.layer2_dropdown.clear()
        labels_layers = [
            layer.name for layer in self.viewer.layers
            if isinstance(layer, napari.layers.Labels)
        ]
        self.layer1_dropdown.addItems(labels_layers)
        self.layer2_dropdown.addItems(labels_layers)
        if current_selection1 in labels_layers:
            self.layer1_dropdown.setCurrentText(current_selection1)
        if current_selection2 in labels_layers:
            self.layer2_dropdown.setCurrentText(current_selection2)

    def combine_labels_layers(self):
        """Combine two labels layers using the selected operation."""
        # Get selected layers
        layer1_name = self.layer1_dropdown.currentText()
        layer2_name = self.layer2_dropdown.currentText()

        if not layer1_name or not layer2_name:
            print("Both labels layers must be selected.")
            return

        layer1 = self.viewer.layers[layer1_name]
        layer2 = self.viewer.layers[layer2_name]

        if not (isinstance(layer1, napari.layers.Labels)
                and isinstance(layer2, napari.layers.Labels)):
            print("Selected layers are not labels layers.")
            return

        # Get operation
        operation = self.operation_dropdown.currentText()

        # Perform operation
        data1 = layer1.data
        data2 = layer2.data

        if data1.shape != data2.shape:
            print("Labels layers must have the same shape.")
            return

        operation_map = {
            "AND": np.logical_and,
            "OR": np.logical_or,
            "NAND": lambda x, y: np.logical_not(np.logical_and(x, y)),
            "NOR": lambda x, y: np.logical_not(np.logical_or(x, y)),
            "XOR": np.logical_xor
        }

        combine_func = operation_map[operation]
        combined_data = combine_func(data1 > 0, data2 > 0).astype(int)

        # Generate new layer name
        new_layer_name = f"{layer1_name} {operation} {layer2_name}"

        # Check if layer with this name already exists
        if new_layer_name in [layer.name for layer in self.viewer.layers]:
            print(
                f"Layer '{new_layer_name}' already exists. Not adding a new layer."
            )
            return

        # Add combined labels layer
        im_temp = self.viewer.add_labels(combined_data, name=new_layer_name)
        im_temp.editable = self.editable_checkbox.isChecked()
        self.layer_manager.add_layer_to_group(LayerType.COMBINED.value,
                                              im_temp)
        print(f"Added combined labels layer: {new_layer_name}")
