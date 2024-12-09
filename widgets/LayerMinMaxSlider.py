import napari
import numpy as np
from qtpy.QtWidgets import QVBoxLayout, QWidget, QLabel, QLineEdit
from superqt import QRangeSlider  # Import QRangeSlider from superqt


class LayerMinMaxSlider(QWidget):
	"""Individual min/max slider for each layer."""

	def __init__(self,
	             layer,
	             slider_scale=1000,
	             override_max=None,
	             override_min=None):
		super().__init__()
		self.layer = layer  # Specific layer for this slider
		self.slider_scale = slider_scale
		self.data_max = override_max if override_max else np.nanmax(layer.data)
		self.data_min = override_min if override_min else np.nanmin(layer.data)
		self.layer_name_label = QLabel(f"Layer: {self.layer.name}")
		self.name = self.layer.name

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

		# Initialize slider based on layer contrast limits
		self.update_slider_to_layer()

	def update_slider_to_layer(self):
		"""Adjust the slider and text boxes to the contrast limits of the layer."""
		contrast_min, contrast_max = self.layer.contrast_limits
		self.min_textbox.setText(f"{contrast_min:.2f}")
		self.max_textbox.setText(f"{contrast_max:.2f}")

		try:
			scaled_min = int(
			    (contrast_min - self.data_min) /
			    (self.data_max - self.data_min) * self.slider_scale)
			scaled_max = int(
			    (contrast_max - self.data_min) /
			    (self.data_max - self.data_min) * self.slider_scale)
		except:
			scaled_min = 0.
			scaled_max = 1.
		self.range_slider.setValue((scaled_min, scaled_max))

	def update_contrast_limits(self, data_min, data_max, contrast_min,
	                           contrast_max):
		"""Update slider and text boxes to new contrast limits for the layer."""
		self.data_min, self.data_max = data_min, data_max
		self.min_textbox.setText(f"{contrast_min:.2f}")
		self.max_textbox.setText(f"{contrast_max:.2f}")
		scaled_min = int((contrast_min - data_min) / (data_max - data_min) *
		                 self.slider_scale)
		scaled_max = int((contrast_max - data_min) / (data_max - data_min) *
		                 self.slider_scale)
		self.range_slider.setValue((scaled_min, scaled_max))

	def update_image(self):
		"""Update the contrast limits for the layer based on the slider values."""
		slider_min, slider_max = self.range_slider.value()
		min_value = slider_min / self.slider_scale * (
		    self.data_max - self.data_min) + self.data_min
		max_value = slider_max / self.slider_scale * (
		    self.data_max - self.data_min) + self.data_min

		if min_value < max_value:
			self.layer.contrast_limits = (min_value, max_value)
			self.min_textbox.setText(f"{min_value:.2f}")
			self.max_textbox.setText(f"{max_value:.2f}")

	def update_contrast_from_text(self):
		"""Update the contrast limits based on values entered in the text boxes."""
		try:
			min_value = float(self.min_textbox.text())
			max_value = float(self.max_textbox.text())
			if min_value < max_value:
				self.layer.contrast_limits = (min_value, max_value)
				scaled_min = int(
				    (min_value - self.data_min) /
				    (self.data_max - self.data_min) * self.slider_scale)
				scaled_max = int(
				    (max_value - self.data_min) /
				    (self.data_max - self.data_min) * self.slider_scale)
				self.range_slider.setValue((scaled_min, scaled_max))
		except ValueError:
			pass  # Ignore invalid input
