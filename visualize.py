import json
import os
import numpy as np
import napari 
from qtpy.QtCore import Qt

from widgets.colormaps import get_all_colormaps
from widgets.SubmitButtons import create_buttons
from widgets.read_write_outputs import read_labels
from widgets.create_sliders import create_sliders
from widgets.LegendWidget import create_legend
from widgets.PointOfViewNavigator import PointOfViewNavigator

def create_napari_visualization(data, band_names, output_filepath, prior_mask=False, prior_manual_labels=False, 
		load_labels=None, dataset_name=None, is_multiangle=False, vis_config_file='./util_files/default_vizconfig.json'):

	viewer = napari.Viewer(show=False)
	viewer.window._qt_window.showFullScreen()
	viewer.show()

	with open(vis_config_file, "r") as file:
		config = json.load(file)

	band_colormaps, label_colormap, mask_colormap = get_all_colormaps(config)
	label_colormap_text = {int(key): value for key,value in config["label_string_text"].items()}
	create_legend(viewer, label_colormap, label_colormap_text, area=config["legend_location"]) 
	
	scene_labels = config['scene_labels']

	name_end = None
	label_layers = []
	label_data = []
	if not prior_mask is None:
		name_end = -1
		orig_labels_layer = viewer.add_labels(prior_mask[:,:,0].astype(int), name=band_names[name_end], colormap=mask_colormap )
		orig_labels_layer.editable = False
		label_layers.append(orig_labels_layer)
		label_data.append(prior_mask[:,:,:].astype(int))

	im_layers = viewer.add_image(data[:,:,:,0], name=band_names[:name_end], channel_axis=2, colormap=band_colormaps)

	if prior_manual_labels:
		man_labels, man_scene_attrs = read_labels(output_filepath, dataset_name, scene_attrs=scene_labels)
		man_labels_layer = viewer.add_labels(man_labels.astype(int), name="Prior Manual Labels", colormap=label_colormap )
		man_labels_layer.editable = False
		label_layers.append(man_labels_layer)
		label_data.append(man_labels.astype(int))

	if load_labels is None:
		edit_data = 1+np.zeros(data[:,:,0,:].shape, dtype=int)
	elif not prior_mask is None and load_labels.upper() == "MASK":
		edit_data = prior_mask[:,:,:].astype(int) 
	elif prior_manual_labels and load_labels.upper() == "MANUAL":
		edit_data = man_labels.astype(int)
		if scene_labels:
			scene_labels = man_scene_attrs
	else:
		raise Warning("load_labels settigs have ambigous settings when compare to prior_mask or prior_manual_labels variables\n defaulting to 'None' value functionality and loading zeros as the Editing Layer")
		edit_data = np.zeros(data[:,:,0,:].shape, dtype=int)

	edit_layer = viewer.add_labels(edit_data[:,:,0], name='Editing', colormap=label_colormap)
	label_layers.append(edit_layer)
	label_data.append(edit_data)
	
	min_max_slider = create_sliders(option=int(config["min_max_slider_option"]), 
		viewer=viewer, 
		layers=im_layers, 
		band_names=band_names[:name_end], 
		area=config["slider_location"])

	if is_multiangle:
		POV_nav = PointOfViewNavigator(viewer,
					im_layers=im_layers,
					min_max_slider=min_max_slider,
					im_data=data,
					label_layers=label_layers,
					label_data=label_data	
					)
		viewer.window.add_dock_widget(POV_nav, name="Point of View Navigator", area='top')

	# TODO: will need to add multi-angle saving -> see pl2.py load labels for logic
	create_buttons(viewer=viewer,
			labels_layer=edit_layer, 
			output_filepath=output_filepath, 
			dataset_name=dataset_name, 
			scene_labels=scene_labels,
			area=config["button_location"])	

	napari.run()

	print("\n\nClose\n\nfgjf")

