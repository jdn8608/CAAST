import json
import numpy as np
import napari 
import tqdm 

from widgets.colormaps import get_all_colormaps
from widgets.SubmitButton_default import create_button as default_button
from widgets.SubmitButton_qual import create_button as qual_button

def single_view_multi_band(data, band_names, output_filepath, prior_labels=False, dataset_name=None, vis_config_file='./util_files/default_vizconfig.json'):
	with open(vis_config_file, "r") as file:
		config = json.load(file)

	band_colormaps, label_colormap, mask_colormap = get_all_colormaps(config)

	viewer = napari.Viewer()
	
	if prior_labels:
		viewer.add_image(data[:,:,:-1], name=band_names[:-1], channel_axis=2,contrast_limits=(0,1), colormap=band_colormaps)
		orig_labels = viewer.add_labels(data[:,:,-1].astype(int), name=band_names[-1], colormap=mask_colormap )
		orig_labels.editable = False
		labels_layer = viewer.add_labels(data[:,:,-1].astype(int), name='Editing', colormap=label_colormap)
	else:
		viewer.add_image(data, name=band_names, channel_axis=2, contrast_limits=(0,1), colormap=band_colormaps)
		labels_layer = viewer.add_labels(1+np.zeros(data[:,:,0].shape, dtype=int), name='Editing', colormap=label_colormap)

	# button info
	output_filepath = "test_new.npy"
	dataset_name = "Manual Labels"
	
	button_location = config["button_location"]
	if config["qual_labels"]==0:
		default_button(viewer, labels_layer, output_filepath, dataset_name, button_location)	
	else:
		qual_labels = config['qual_labels']
		print(qual_labels)
		qual_button(viewer, labels_layer, output_filepath, qual_labels, dataset_name, button_location)	

	napari.run()
	viewer.close()

	print("\n\nClose\n\nfgjf")

