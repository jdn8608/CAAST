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
)
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier


class MachineLearningWidget(QWidget):
    """Widget that trains a model on labeled pixels and applies predictions."""

    def __init__(self, viewer: napari.Viewer, layer_manager=None):
        super().__init__()
        self.viewer = viewer
        self.layer_manager = layer_manager
        self.model = None
        self.input_layer_names = []
        self.fill_value = -2

        self._build_ui()

        # Update layer lists when viewer layers change
        self.viewer.layers.events.inserted.connect(self.update_layers)
        self.viewer.layers.events.removed.connect(self.update_layers)
        self.update_layers()

    def _build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Labels layer selector
        labels_layout = QHBoxLayout()
        labels_layout.addWidget(QLabel("Labels layer"))
        self.labels_dropdown = QComboBox()
        labels_layout.addWidget(self.labels_dropdown)
        layout.addLayout(labels_layout)

        # Input layers list (multi-select)
        inputs_layout = QHBoxLayout()
        inputs_layout.addWidget(QLabel("Input layers"))
        self.input_list = QListWidget()
        self.input_list.setSelectionMode(QListWidget.MultiSelection)
        inputs_layout.addWidget(self.input_list)
        layout.addLayout(inputs_layout)

        # Model type selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model"))
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(["Random Forest", "Gradient Boosting"])
        model_layout.addWidget(self.model_dropdown)
        layout.addLayout(model_layout)

        # Fill value selection
        fill_layout = QHBoxLayout()
        fill_layout.addWidget(QLabel("Fill value"))
        self.fill_edit = QLineEdit("-2")
        fill_layout.addWidget(self.fill_edit)
        layout.addLayout(fill_layout)

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
        self.train_button.clicked.connect(self.train_model)
        self.apply_button.clicked.connect(self.apply_model)

    def update_layers(self, event=None):
        """Populate layer selectors with current viewer layers."""
        # Update labels dropdown
        current_label = self.labels_dropdown.currentText()
        self.labels_dropdown.clear()
        labels_layers = [
            layer.name for layer in self.viewer.layers
            if isinstance(layer, napari.layers.Labels)
        ]
        self.labels_dropdown.addItems(labels_layers)
        if current_label in labels_layers:
            self.labels_dropdown.setCurrentText(current_label)

        # Update input layer list
        selected = {item.text() for item in self.input_list.selectedItems()}
        self.input_list.clear()
        image_layers = [
            layer.name for layer in self.viewer.layers
            if isinstance(layer, napari.layers.Image)
        ]
        for name in image_layers:
            item = QListWidgetItem(name)
            self.input_list.addItem(item)
            if name in selected:
                item.setSelected(True)

    def _collect_features(self, layer_names):
        """Return stacked feature array for given image layers."""
        features = [self.viewer.layers[name].data.ravel() for name in layer_names]
        return np.stack(features, axis=1)

    def train_model(self):
        """Train the selected model using labeled pixels."""
        labels_name = self.labels_dropdown.currentText()
        if not labels_name:
            self.status_label.setText("Select a labels layer.")
            return

        input_names = [item.text() for item in self.input_list.selectedItems()]
        if not input_names:
            self.status_label.setText("Select at least one input layer.")
            return

        try:
            self.fill_value = int(self.fill_edit.text())
        except ValueError:
            self.status_label.setText("Invalid fill value.")
            return

        labels_layer = self.viewer.layers[labels_name]
        labels_data = labels_layer.data.ravel()
        X = self._collect_features(input_names)
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
        self.input_layer_names = input_names
        self.apply_button.setEnabled(True)

    def apply_model(self):
        """Apply the trained model to fill unlabeled pixels."""
        if self.model is None:
            self.status_label.setText("Train a model first.")
            return

        labels_name = self.labels_dropdown.currentText()
        if not labels_name:
            self.status_label.setText("Select a labels layer.")
            return

        labels_layer = self.viewer.layers[labels_name]
        labels_data = labels_layer.data
        flat_labels = labels_data.ravel()
        X = self._collect_features(self.input_layer_names)
        mask = flat_labels == self.fill_value
        if not np.any(mask):
            self.status_label.setText("No pixels to fill.")
            return

        flat_labels[mask] = self.model.predict(X[mask])
        labels_layer.data = flat_labels.reshape(labels_data.shape)
        self.status_label.setText("Applied model predictions.")
