import numpy as np
import napari
from qtpy.QtWidgets import QVBoxLayout, QWidget, QSlider, QLabel, QLineEdit
from qtpy.QtCore import Qt
from superqt import QRangeSlider

class PointOfViewNavigator(QWidget):
    def __init__(self, viewer, im_layers, min_max_slider, im_data, label_layers, label_data, view_text, angles):
        super().__init__()
        self.viewer = viewer
        self.im_layers = im_layers
        self.min_max_slider = min_max_slider
        self.im_data = im_data
        self.label_layers = label_layers
        self.label_data = label_data
        self.num_views = im_data.shape[3]  # Number of points of view
        self.view_text = view_text 
        self.angles = angles
        self.data = self.label_data[-1]  # editing labels is always listed in last entry	

        # Setup layout
        layout = QVBoxLayout()
        self.view_label = QLabel(f"Camera: {self.view_text[0]} View Angle: {self.angles[0]}\u00B0")
        self.view_label.setAlignment(Qt.AlignCenter) 
        layout.addWidget(self.view_label)

        # Point of View slider
        self.view_slider = QSlider(Qt.Horizontal)
        self.view_slider.setMinimum(0)
        self.view_slider.setMaximum(self.num_views - 1)
        self.view_slider.setValue(0)
        self.view_slider.setTickPosition(QSlider.TicksBelow)
        self.view_slider.setTickInterval(1)
        self.view_slider.valueChanged.connect(self.update_all_layers_view)

        layout.addWidget(self.view_slider)
        self.setLayout(layout)

        # Set focus for handling key events
        self.setFocusPolicy(Qt.StrongFocus)

        # Connect viewer's key events to this widget
        self.viewer.bind_key('Left', self.go_left)
        self.viewer.bind_key('Right', self.go_right)

    def update_all_layers_view(self):
        """Update all layers to display the selected point of view."""
        current_view = self.view_slider.value()
        self.view_label.setText(f"Camera: {self.view_text[current_view]} View Angle: {self.angles[current_view]}\u00B0")
        self.update_imagery(current_view)
        self.update_labels(current_view)

    def update_imagery(self, current_view=1):
        for channel_index, im_layer in enumerate(self.im_layers):
            if isinstance(im_layer, napari.layers.Image):
                # Update Image layer with the appropriate channel and current view slice
                im_layer.data = self.im_data[:, :, channel_index, current_view]

    def update_labels(self, current_view=1):
        for label_layer, l_data in zip(self.label_layers,self.label_data):
            if isinstance(label_layer, napari.layers.Labels):
                # Update Image layer with the appropriate channel and current view slice
                label_layer.data = l_data[:, :, current_view]

    def go_left(self, _event=None):
        """Navigate to the previous view if possible."""
        if self.view_slider.value() > 0:
            self.view_slider.setValue(self.view_slider.value() - 1)

    def go_right(self, _event=None):
        """Navigate to the next view if possible."""
        if self.view_slider.value() < self.num_views - 1:
            self.view_slider.setValue(self.view_slider.value() + 1)
