"""Widget for training and applying simple machine learning models to labels."""

import numpy as np
import napari
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QDialog,
    QDialogButtonBox,
)
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

from util.LayerType import LayerType


class MachineLearningWidget(QWidget):
    """Widget that trains a model on labeled pixels and applies predictions."""

    def __init__(self, viewer: napari.Viewer, layer_manager=None):
        super().__init__()
        self.viewer = viewer
        self.layer_manager = layer_manager

        self.model = None
        self.labels_layer_name = ""
        self.input_layer_names = []
        self.fill_value = -2

        self._build_ui()

    # ------------------------------------------------------------------ UI ----
    def _build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Model selection remains visible on the tab
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model"))
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(["Random Forest", "Gradient Boosting"])
        model_layout.addWidget(self.model_dropdown)
        layout.addLayout(model_layout)

        # Output layer name
        out_layout = QHBoxLayout()
        out_layout.addWidget(QLabel("Output layer name"))
        self.output_name_edit = QLineEdit("ML Labels")
        out_layout.addWidget(self.output_name_edit)
        layout.addLayout(out_layout)

        # Button to open training-parameter dialog
        self.params_button = QPushButton("Set Model Training Parameters")
        layout.addWidget(self.params_button)

        # Train and apply buttons
        button_layout = QHBoxLayout()
        self.train_button = QPushButton("Train")
        self.apply_button = QPushButton("Apply")
        self.apply_button.setEnabled(False)
        button_layout.addWidget(self.train_button)
        button_layout.addWidget(self.apply_button)
        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Connect signals
        self.params_button.clicked.connect(self.open_params_dialog)
        self.train_button.clicked.connect(self.train_model)
        self.apply_button.clicked.connect(self.apply_model)

    # --------------------------------------------------------------- helpers ----
    def _collect_features(self, layer_names):
        """Return stacked feature array for given image layers."""
        features = [self.viewer.layers[name].data.ravel() for name in layer_names]
        return np.stack(features, axis=1)

    def open_params_dialog(self):
        """Open dialog to set labels, inputs, and fill value."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Model Training Parameters")
        layout = QVBoxLayout(dialog)

        # Labels layer selector
        labels_layout = QHBoxLayout()
        labels_layout.addWidget(QLabel("Labels layer"))
        labels_dropdown = QComboBox()
        labels_layout.addWidget(labels_dropdown)
        layout.addLayout(labels_layout)

        # Input layers list
        inputs_layout = QHBoxLayout()
        inputs_layout.addWidget(QLabel("Input layers"))
        input_list = QListWidget()
        input_list.setSelectionMode(QListWidget.MultiSelection)
        inputs_layout.addWidget(input_list)
        layout.addLayout(inputs_layout)

        # Fill value selection
        fill_layout = QHBoxLayout()
        fill_layout.addWidget(QLabel("Fill value"))
        fill_edit = QLineEdit(str(self.fill_value))
        fill_layout.addWidget(fill_edit)
        layout.addLayout(fill_layout)

        # Populate layer widgets with current viewer state
        label_layers = [
            layer.name for layer in self.viewer.layers
            if isinstance(layer, napari.layers.Labels)
        ]
        labels_dropdown.addItems(label_layers)
        if self.labels_layer_name in label_layers:
            labels_dropdown.setCurrentText(self.labels_layer_name)

        image_layers = [
            layer.name for layer in self.viewer.layers
            if isinstance(layer, napari.layers.Image)
        ]
        for name in image_layers:
            item = QListWidgetItem(name)
            input_list.addItem(item)
            if name in self.input_layer_names:
                item.setSelected(True)

        # OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        if dialog.exec_():
            labels_name = labels_dropdown.currentText()
            input_names = [item.text() for item in input_list.selectedItems()]
            try:
                fill_val = int(fill_edit.text())
            except ValueError:
                self.status_label.setText("Invalid fill value.")
                return

            if not labels_name or not input_names:
                self.status_label.setText("Select labels and input layers.")
                return

            self.labels_layer_name = labels_name
            self.input_layer_names = input_names
            self.fill_value = fill_val
            self.status_label.setText("Training parameters set.")

    # --------------------------------------------------------------- actions ----
    def train_model(self):
        """Train the selected model using labeled pixels."""
        if not self.labels_layer_name or not self.input_layer_names:
            self.status_label.setText("Set training parameters first.")
            return

        labels_layer = self.viewer.layers[self.labels_layer_name]
        labels_data = labels_layer.data.ravel()
        X = self._collect_features(self.input_layer_names)
        mask = labels_data != self.fill_value
        if not np.any(mask):
            self.status_label.setText("No labeled pixels found.")
            return

        X_train = X[mask]
        y_train = labels_data[mask]

        model_type = self.model_dropdown.currentText()
        if model_type == "Random Forest":
            model = RandomForestClassifier()
        else:
            model = GradientBoostingClassifier()

        model.fit(X_train, y_train)
        train_acc = (model.predict(X_train) == y_train).mean()
        self.status_label.setText(
            f"Trained {model_type} | accuracy {train_acc:.3f}")
        self.model = model
        self.apply_button.setEnabled(True)

    def apply_model(self):
        """Apply the trained model to fill unlabeled pixels in a new layer."""
        if self.model is None:
            self.status_label.setText("Train a model first.")
            return

        if not self.labels_layer_name:
            self.status_label.setText("Set training parameters first.")
            return

        output_name = self.output_name_edit.text().strip()
        if not output_name:
            self.status_label.setText("Provide output layer name.")
            return

        existing_names = [layer.name for layer in self.viewer.layers]
        if output_name in existing_names:
            self.status_label.setText("Layer name already in use.")
            return

        labels_layer = self.viewer.layers[self.labels_layer_name]
        labels_data = labels_layer.data
        flat_labels = labels_data.ravel().copy()
        X = self._collect_features(self.input_layer_names)
        mask = flat_labels == self.fill_value
        if not np.any(mask):
            self.status_label.setText("No pixels to fill.")
            return

        flat_labels[mask] = self.model.predict(X[mask])
        new_data = flat_labels.reshape(labels_data.shape)
        new_layer = self.viewer.add_labels(new_data, name=output_name)
        if self.layer_manager is not None:
            self.layer_manager.add_layer_to_group(
                LayerType.MANUAL_LABELS.value, new_layer)

        self.status_label.setText(
            f"Created layer '{output_name}' with predictions.")

