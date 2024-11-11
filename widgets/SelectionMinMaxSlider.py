import napari
import numpy as np
from qtpy.QtWidgets import QVBoxLayout, QWidget, QLabel, QLineEdit
from superqt import QRangeSlider  # Import QRangeSlider from superqt

class SelectionMinMaxSlider(QWidget):
    """Slider widget for controlling min and max contrast limits of the selected layer."""
    def __init__(self, viewer, slider_scale=1000):
        super().__init__()
        self.viewer = viewer
        self.layer = None  # Selected layer
        self.slider_scale = slider_scale
        self.data_min, self.data_max = None, None
        self.layer_name_label = QLabel("Selected Layer")

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.layer_name_label)

        # Min and Max text boxes
        self.min_textbox = QLineEdit()
        self.min_textbox.setPlaceholderText("Min")
        self.min_textbox.returnPressed.connect(self.update_contrast_from_text)
        layout.addWidget(self.min_textbox)

        self.max_textbox = QLineEdit()
        self.max_textbox.setPlaceholderText("Max")
        self.max_textbox.returnPressed.connect(self.update_contrast_from_text)
        layout.addWidget(self.max_textbox)

        # Range slider for min/max control
        layout.addWidget(QLabel("Min/Max Range Slider"))
        self.range_slider = QRangeSlider()
        self.range_slider.setOrientation(1)  # Horizontal
        self.range_slider.setRange(0, self.slider_scale)
        self.range_slider.valueChanged.connect(self.update_image)
        layout.addWidget(self.range_slider)

        self.setLayout(layout)

        # Connect to layer selection events in the viewer
        viewer.layers.selection.events.changed.connect(self.update_on_selection)

    def update_on_selection(self, event):
        """Update the min/max slider based on the currently selected layer."""
        selected_layers = list(self.viewer.layers.selection)
        if selected_layers:
            self.layer = selected_layers[0]
            self.layer_name_label.setText(f"Selected Layer: {self.layer.name}")
            
            # Only update the slider if the layer is an Image layer
            if isinstance(self.layer, napari.layers.Image):
                self.update_slider_to_layer()
            else:
                # Clear the slider and text boxes if a non-Image layer is selected
                self.clear_slider()

    def update_slider_to_layer(self):
        """Adjust the slider and text boxes to the contrast limits of the selected layer."""
        if self.layer is not None and isinstance(self.layer, napari.layers.Image):
            layer_data = self.layer.data
            contrast_min, contrast_max = self.layer.contrast_limits
            self.data_min, self.data_max = layer_data.min(), layer_data.max()

            # Update slider and text boxes to reflect current contrast limits
            self.min_textbox.setText(f"{contrast_min:.2f}")
            self.max_textbox.setText(f"{contrast_max:.2f}")

            try:
                scaled_min = int((contrast_min - self.data_min) / (self.data_max - self.data_min) * self.slider_scale)
                scaled_max = int((contrast_max - self.data_min) / (self.data_max - self.data_min) * self.slider_scale)
            except:
                scaled_min = 0.
                scaled_max = 1.

            self.range_slider.setValue((scaled_min, scaled_max))

    def clear_slider(self):
        """Clear the slider and text boxes when a non-Image layer is selected."""
        self.min_textbox.clear()
        self.max_textbox.clear()
        self.range_slider.setValue((0, self.slider_scale))

    def update_image(self):
        """Update the contrast limits for the selected layer based on the slider values."""
        if self.layer and isinstance(self.layer, napari.layers.Image) and self.data_min is not None and self.data_max is not None:
            slider_min, slider_max = self.range_slider.value()
            min_value = slider_min / self.slider_scale * (self.data_max - self.data_min) + self.data_min
            max_value = slider_max / self.slider_scale * (self.data_max - self.data_min) + self.data_min

            if min_value < max_value:
                self.layer.contrast_limits = (min_value, max_value)
                self.min_textbox.setText(f"{min_value:.2f}")
                self.max_textbox.setText(f"{max_value:.2f}")

    def update_contrast_from_text(self):
        """Update the contrast limits based on values entered in the text boxes."""
        if self.layer and isinstance(self.layer, napari.layers.Image):
            try:
                min_value = float(self.min_textbox.text())
                max_value = float(self.max_textbox.text())
                if min_value < max_value:
                    self.layer.contrast_limits = (min_value, max_value)
                    scaled_min = int((min_value - self.data_min) / (self.data_max - self.data_min) * self.slider_scale)
                    scaled_max = int((max_value - self.data_min) / (self.data_max - self.data_min) * self.slider_scale)
                    self.range_slider.setValue((scaled_min, scaled_max))
            except ValueError:
                pass  # Ignore invalid input
        """Update the min/max slider based on the currently selected layer."""
        selected_layers = list(self.viewer.layers.selection)
        if selected_layers:
            self.layer = selected_layers[0]
            self.layer_name_label.setText(f"Selected Layer: {self.layer.name}")
            self.update_slider_to_layer()

    def update_slider_to_layer(self):
        """Adjust the slider and text boxes to the contrast limits of the selected layer."""
        if self.layer is not None:
            layer_data = self.layer.data
            contrast_min, contrast_max = self.layer.contrast_limits
            self.data_min, self.data_max = layer_data.min(), layer_data.max()

            # Update slider and text boxes to reflect current contrast limits
            self.min_textbox.setText(f"{contrast_min:.2f}")
            self.max_textbox.setText(f"{contrast_max:.2f}")
            scaled_min = int((contrast_min - self.data_min) / (self.data_max - self.data_min) * self.slider_scale)
            scaled_max = int((contrast_max - self.data_min) / (self.data_max - self.data_min) * self.slider_scale)
            self.range_slider.setValue((scaled_min, scaled_max))

    def update_image(self):
        """Update the contrast limits for the selected layer based on the slider values."""
        if self.layer and self.data_min is not None and self.data_max is not None:
            slider_min, slider_max = self.range_slider.value()
            min_value = slider_min / self.slider_scale * (self.data_max - self.data_min) + self.data_min
            max_value = slider_max / self.slider_scale * (self.data_max - self.data_min) + self.data_min

            if min_value < max_value:
                self.layer.contrast_limits = (min_value, max_value)
                self.min_textbox.setText(f"{min_value:.2f}")
                self.max_textbox.setText(f"{max_value:.2f}")

    def update_contrast_from_text(self):
        """Update the contrast limits based on values entered in the text boxes."""
        if self.layer:
            try:
                min_value = float(self.min_textbox.text())
                max_value = float(self.max_textbox.text())
                if min_value < max_value:
                    self.layer.contrast_limits = (min_value, max_value)
                    scaled_min = int((min_value - self.data_min) / (self.data_max - self.data_min) * self.slider_scale)
                    scaled_max = int((max_value - self.data_min) / (self.data_max - self.data_min) * self.slider_scale)
                    self.range_slider.setValue((scaled_min, scaled_max))
            except ValueError:
                pass  # Ignore invalid input
