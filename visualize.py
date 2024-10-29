import json
import os
import numpy as np
import napari 

from widgets.colormaps import get_all_colormaps
from widgets.SubmitButtons import create_buttons

def single_view_multi_band(data, band_names, output_filepath, prior_mask=False, prior_manual_labels=False, 
		load_labels=None, dataset_name=None, vis_config_file='./util_files/default_vizconfig.json'):
	with open(vis_config_file, "r") as file:
		config = json.load(file)

	band_colormaps, label_colormap, mask_colormap = get_all_colormaps(config)

	viewer = napari.Viewer()
	
	#if prior_manual_labels:
	#LOAD NON-EDIT LAYER OF PRIORS -> NEED TO PASS DATA OR LOAD IT HERE		
	if prior_mask:
		viewer.add_image(data[:,:,:-1], name=band_names[:-1], channel_axis=2,contrast_limits=(0,1), colormap=band_colormaps)
		orig_labels = viewer.add_labels(data[:,:,-1].astype(int), name=band_names[-1], colormap=mask_colormap )
		orig_labels.editable = False
	else:
		viewer.add_image(data, name=band_names, channel_axis=2, contrast_limits=(0,1), colormap=band_colormaps)

	if load_labels is None:
		labels_layer = viewer.add_labels(1+np.zeros(data[:,:,0].shape, dtype=int), name='Editing', colormap=label_colormap)
	elif prior_mask and load_labels == "mask":
		labels_layer = viewer.add_labels(data[:,:,-1].astype(int), name='Editing', colormap=label_colormap)
	#elif prior_manual_labels and load_labels == "manual":
	# lOAD PRIOR MANUAL LABELS AS THE EDITING LABELS
	else:
		raise Warning("load_labels settigs have ambigous settings when compare to prior_mask or prior_manual_labels variables\n defaulting to 'None' value functionality and loading zeros as the Editing Layer")
		labels_layer = viewer.add_labels(np.zeros(data[:,:,0].shape, dtype=int), name='Editing', colormap=label_colormap)

	button_location = config["button_location"]
	qual_labels = config['qual_labels']
	load_qual = not qual_labels==0
	create_buttons(viewer=viewer,
			labels_layer=labels_layer, 
			output_filepath=output_filepath, 
			dataset_name=dataset_name, 
			load_qual=True,
			qual_labels=qual_labels,
			area=button_location)	

	napari.run()
	viewer.close()

	print("\n\nClose\n\nfgjf")

