import numpy as np
import h5py as h5
import xarray as xr

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox, QPushButton, QWidget, QLabel

def save_labels(data, qual_dict, output_filepath, dataset_name):

		filetype = output_filepath.split('.')[-1]
		if filetype == 'npy':
			np.save(output_filepath, data)
			if qual_dict:
				qual_attributes = {label: combo_box.currentText() for label, combo_box in qual_dict.items()}	
				print(qual_attributes)
		elif filetype == 'hdf':
			out_file = h5.File(output_filepath, "w")
			out_file.create_dataset(dataset_name, data=data)
			out_file.close()
		elif filetype == 'nc':
			da = xr.DataArray(
				data,
				dims=("y", "x"),
				name=dataset_name
			)
			ds = xr.Dataset({dataset_name: da}, attrs=qual_attributes)
			ds.to_netcdf(output_filepath)
		else:
			raise Exception(f"filetype '{filetype}' id not currently supported for saving files.\n please use a different filetype for output, or add functionality for this filetype")


def create_buttons(viewer, labels_layer, output_filepath, dataset_name=None, load_qual=False, 
			qual_labels=None, area="top"):


	# Create a save button widget
	save_button_widget = QWidget()
	save_button_layout = QVBoxLayout()


	if load_qual:
		qual_dict = dict((q,QComboBox()) for q in qual_labels)


		grid_layout = QGridLayout()
		grid_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins around the grid layout
		grid_layout.setSpacing(10)

		# Add label and dropdown for each qualitative label in the grid layout
		max_columns = 4
		row = 0
		col = 0

		# Add label and dropdown for each qualitative label
		for label_text, combo_box in qual_dict.items():
			combo_box.addItems(["Unclear", "Yes", "No"])
			combo_box.setCurrentText("Unclear")  # Set "Unclear" as default
			combo_box.setFixedWidth(200)

			label_widget = QLabel(label_text.replace("_", " ").capitalize())
			grid_layout.addWidget(label_widget, row, col)
			grid_layout.addWidget(combo_box, row, col + 1)

			col += 2
			if col >= max_columns * 2:  # Move to the next row after 4 pairs
				col = 0
				row += 1


		save_button_layout.addLayout(grid_layout)
	else:
		qual_dict={}
	
	save_button = QPushButton("Save Labels & Flags")
	save_button.clicked.connect(lambda: save_labels(labels_layer.data, qual_dict, output_filepath, dataset_name))
	save_button_layout.addWidget(save_button)
	save_button_widget.setLayout(save_button_layout)

        # Add the button widget to Napari's dock
	viewer.window.add_dock_widget(save_button_widget, area=area)
