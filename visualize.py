import json
import numpy as np
import napari 
import tqdm 

from napari.utils.colormaps import Colormap
from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap


def _get_custom_colormap(options, plural=False):

	with open('./util_files/custom_colormaps.json', "r") as file:
		custom_colormaps = json.load(file)
	return {int(key):[float(item) for item in values] for key,values in custom_colormaps[options].items()}
	
	

def get_colormap(option):
	# get band colormap(s)	
	colormap = option 
	if colormap[0:7] == 'custom_':
		colormap = _get_custom_colormap(colormap[7:])
	return colormap

def get_colormaps_from_config(config, option_name):
	if isinstance(config[option_name], str):
		return get_colormap(config[option_name])
	elif isinstance(config[option_name], list):
		return [get_colormap(opt) for opt in config[option_name]]
	elif config[option_name] is None:
		return None
	else:
		raise Exception("Erro within visualization config file: 'f{option_name}' option is of invalid type 'f{type(config['band_color_maps'])}'")

def get_all_colormaps(config):
	return tuple([get_colormaps_from_config(config, x) for x in ['band_colormaps','label_colormap','mask_colormap']])

def single_view_multi_band(data, band_names, prior_labels=False, vis_config_file='./util_files/default_vizconfig.json'):
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

	napari.run()
	viewer.close()



