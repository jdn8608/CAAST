import json
import os
import numpy as np
import napari 

from widgets.colormaps import get_all_colormaps
from widgets.SubmitButtons import create_buttons
from widgets.read_write_outputs import read_labels
from widgets.create_sliders import create_sliders

def single_view_multi_band(data, band_names, output_filepath, prior_mask=False, prior_manual_labels=False, 
		load_labels=None, dataset_name=None, vis_config_file='./util_files/default_vizconfig.json'):
	with open(vis_config_file, "r") as file:
		config = json.load(file)

	button_location = config["button_location"]
	scene_labels = config['scene_labels']

	band_colormaps, label_colormap, mask_colormap = get_all_colormaps(config)

	viewer = napari.Viewer()
	
	if not prior_mask is None:
		viewer.add_image(data[:,:,:], name=band_names[:-1], channel_axis=2,contrast_limits=(0,1), colormap=band_colormaps)
		orig_labels_layer = viewer.add_labels(prior_mask.astype(int), name=band_names[-1], colormap=mask_colormap )
		orig_labels_layer.editable = False
	else:
		viewer.add_image(data, name=band_names, channel_axis=2, contrast_limits=(0,1), colormap=band_colormaps)
	if prior_manual_labels:
		man_labels, man_scene_attrs = read_labels(output_filepath, dataset_name, scene_attrs=scene_labels)
		print(man_scene_attrs)
		man_labels_layer = viewer.add_labels(man_labels.astype(int), name="Prior Manual Labels", colormap=label_colormap )
		man_labels_layer.editable = False

	if load_labels is None:
		labels_layer = viewer.add_labels(1+np.zeros(data[:,:,0].shape, dtype=int), name='Editing', colormap=label_colormap)
	elif not prior_mask is None and load_labels.upper() == "MASK":
		labels_layer = viewer.add_labels(prior_mask.astype(int), name='Editing', colormap=label_colormap)
	elif prior_manual_labels and load_labels.upper() == "MANUAL":
		labels_layer = viewer.add_labels(man_labels.astype(int), name='Editing', colormap=label_colormap)
		if scene_labels:
			scene_labels = man_scene_attrs
	else:
		raise Warning("load_labels settigs have ambigous settings when compare to prior_mask or prior_manual_labels variables\n defaulting to 'None' value functionality and loading zeros as the Editing Layer")
		labels_layer = viewer.add_labels(np.zeros(data[:,:,0].shape, dtype=int), name='Editing', colormap=label_colormap)

	print(scene_labels)
	create_buttons(viewer=viewer,
			labels_layer=labels_layer, 
			output_filepath=output_filepath, 
			dataset_name=dataset_name, 
			scene_labels=scene_labels,
			area=button_location)	

	napari.run()
	viewer.close()

	print("\n\nClose\n\nfgjf")

