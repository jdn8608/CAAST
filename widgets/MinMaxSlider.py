import napari
import numpy as np
from qtpy.QtWidgets import QVBoxLayout, QWidget, QLabel, QLineEdit
from superqt import QRangeSlider  # Import QRangeSlider from superqt

class MinMaxSlider(QWidget):
    def __init__(self, layer, slider_scale=1000):
        super().__init__()
        self.layer = layer
        self.slider_scale = slider_scale  # Scale factor for fine-grained slider control

        # Setup layout
        layout = QVBoxLayout()

        # Label to display the name of the layer
        #self.layer_name_label = QLabel(f"Layer: {self.layer.name}")
        #layout.addWidget(self.layer_name_label)

        # Add text boxes for current min/max values
        self.min_textbox = QLineEdit()
        self.min_textbox.setPlaceholderText("Min")
        self.min_textbox.returnPressed.connect(self.update_contrast_from_text)
        layout.addWidget(self.min_textbox)

        self.max_textbox = QLineEdit()
        self.max_textbox.setPlaceholderText("Max")
        self.max_textbox.returnPressed.connect(self.update_contrast_from_text)
        layout.addWidget(self.max_textbox)

        # Create range slider for min/max control
        layout.addWidget(QLabel("Min/Max Range Slider"))
        self.range_slider = QRangeSlider()
        self.range_slider.setOrientation(1)  # Horizontal
        self.range_slider.setRange(0, self.slider_scale)  # Set initial range to scaled range
        self.range_slider.valueChanged.connect(self.update_image)
        layout.addWidget(self.range_slider)

        self.setLayout(layout)

        # Initialize slider and text box with the current layer's data range and contrast limits
        self.reset_slider_range()

    def reset_slider_range(self):
        """Set the range and values of the slider to match the data range of the assigned layer."""
        # Get the current layer's data min and max
        data_min = self.layer.data.min()
        data_max = self.layer.data.max()
        self.data_min = data_min
        self.data_max = data_max

        # Retrieve the initial contrast limits
        contrast_min, contrast_max = self.layer.contrast_limits

        # Set the text boxes to show the current min/max contrast values
        self.min_textbox.setText(f"{contrast_min:.2f}")
        self.max_textbox.setText(f"{contrast_max:.2f}")

        # Set slider to full range and scale contrast limits to slider range
        self.range_slider.setRange(0, self.slider_scale)
        scaled_min = int((contrast_min - data_min) / (data_max - data_min) * self.slider_scale)
        scaled_max = int((contrast_max - data_min) / (data_max - data_min) * self.slider_scale)
        self.range_slider.setValue((scaled_min, scaled_max))

    def update_image(self):
        """Update the layer's contrast limits based on the slider values."""
        # Get the current slider values and map them back to the original data range
        slider_min, slider_max = self.range_slider.value()
        min_value = slider_min / self.slider_scale * (self.data_max - self.data_min) + self.data_min
        max_value = slider_max / self.slider_scale * (self.data_max - self.data_min) + self.data_min

        # Update the layer's contrast limits if values are valid
        if min_value < max_value:
            self.layer.contrast_limits = (min_value, max_value)

            # Update the text boxes to show the current min and max values
            self.min_textbox.setText(f"{min_value:.2f}")
            self.max_textbox.setText(f"{max_value:.2f}")

    def update_contrast_from_text(self):
        """Update the contrast limits based on the values entered in the text boxes."""
        try:
            # Get the values from the text boxes
            min_value = float(self.min_textbox.text())
            max_value = float(self.max_textbox.text())

            # Validate and set the contrast limits if the values are correct
            if min_value < max_value:
                self.layer.contrast_limits = (min_value, max_value)

                # Update the range slider to match the new contrast limits
                scaled_min = int((min_value - self.data_min) / (self.data_max - self.data_min) * self.slider_scale)
                scaled_max = int((max_value - self.data_min) / (self.data_max - self.data_min) * self.slider_scale)
                self.range_slider.setValue((scaled_min, scaled_max))
        except ValueError:
            pass  # Ignore invalid input
