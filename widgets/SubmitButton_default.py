import numpy as np
import h5py as h5
import xarray as xr

from qtpy.QtWidgets import QVBoxLayout, QPushButton, QWidget

def save_labels(data, OUTPUT_FILEPATH, dataset_name):
                filetype = OUTPUT_FILEPATH.split('.')[-1]
                if filetype == 'npy':
                        np.save(OUTPUT_FILEPATH, data)
                elif filetype == 'hdf':
                        out_file = h5.File(OUTPUT_FILEPATH, "w")
                        out_file.create_dataset(dataset_name, data=data)
                        out_file.close()
                elif filetype == 'nc':
                        da = xr.DataArray(
                                data,
                                dims=("y", "x"),
                                name=dataset_name
                                )
                        da.to_netcdf(OUTPUT_FILEPATH)
                else:
                        raise Exception(f"filetype '{filetype}' id not currently supported for saving files.\n please use a different filetype for output, or add functionality for this filetype")


def create_button(viewer, labels_layer, OUTPUT_FILEPATH, dataset_name=None, area="top"):
	# Create a save button widget
        save_button_widget = QWidget()
        save_button_layout = QVBoxLayout()
        save_button = QPushButton("Save Labels")
        save_button.clicked.connect(lambda: save_labels(labels_layer.data, OUTPUT_FILEPATH, dataset_name))
        save_button_layout.addWidget(save_button)
        save_button_widget.setLayout(save_button_layout)

        # Add the button widget to Napari's dock
        viewer.window.add_dock_widget(save_button_widget, area=area)
