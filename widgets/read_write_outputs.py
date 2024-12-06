import numpy as np
import h5py as h5
import xarray as xr
import datetime
from tqdm import tqdm
import os
import errno

def save_labels(labels, output_filepath, dataset_name, views, scene_labels_dict):
		print(f"{datetime.datetime.now()}: labels saved to {output_filepath}")

		filetype = output_filepath.split('.')[-1]
		if scene_labels_dict:
			scene_attributes = {label: combo_box.currentText() for label, combo_box in scene_labels_dict.items()}
			scene_labels_write(format_scene_label_file(output_filepath), scene_attributes)

		if filetype == 'npy':
			writer = npy_write
		elif filetype == 'hdf' or filetype=='hdf5':
			writer = hdf_write
		elif filetype == 'nc':
			writer = nc_write
		else:
			raise Exception(f"filetype '{filetype}' id not currently supported for saving files.\n please use a different filetype for output, or add functionality for this filetype")
		
		for v, view in enumerate(tqdm(views, desc="Saving File(s)")):
			writer(format_output_filepath_views(output_filepath, view), dataset_name, labels[:,:,v])

def format_output_filepath_views(filepath, view):
	return filepath.replace('<view>',view)

def npy_read(filepath, dataset_name):
	d = np.load(filepath, allow_pickle=True)
	return np.load(filepath, allow_pickle=True)

def npy_write(filepath, dataset_name, data):
	np.save(filepath, data)

def nc_read(filepath, dataset_name):
	ds = xr.open_dataset(filepath)
	data = ds[dataset_name].values  # Assuming "labels" is the dataset name
	ds.close()
	return data

def nc_write(filepath, dataset_name, data):
	da = xr.DataArray(
		data,
		dims=("y", "x"),
		name=dataset_name
	)
	ds = xr.Dataset({dataset_name:da})
	ds.to_netcdf(filepath)
	

def hdf_read(filepath, dataset_name):
	h5_dataset = h5.File(filepath, "r") 
	data = h5_dataset[dataset_name][:]
	h5_dataset.close()
	return data

def hdf_write(filepath, dataset_name, data):
	out_file = h5.File(filepath, "w")
	h5_dataset = out_file.create_dataset(dataset_name, data=data)
	out_file.close()

def format_scene_label_file(filepath):
	return f'{os.path.splitext(filepath)[0]}_scenelabels.txt'.replace("<view>","ALL")

def scene_labels_read(filepath):	
	scene_attributes = {}
	with open(filepath, 'r') as txt_file:	
		for line in txt_file:
			key, value = tuple(line.split(" : "))
			value = value.strip()
			scene_attributes[key] = value
	return scene_attributes

def scene_labels_write(filepath, scene_attributes):	
	
	with open(filepath,"w") as txt_file:
		for key, value in zip(scene_attributes.keys(), scene_attributes.values()):
			txt_file.write(f"{key} : {value}\n")	
		
	return

def check_file_exists(filepath):
	if os.path.exists(filepath):
		return
	else:
		raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filepath) 

def read_labels(output_filepath, dataset_name, views, scene_attrs=False):
		if scene_attrs:
			scene_label_filepath = format_scene_label_file(output_filepath) 
			check_file_exists(scene_label_filepath)
			scene_attributes = scene_labels_read(scene_label_filepath)

		filetype = output_filepath.split('.')[-1]
		if filetype == 'npy':
			reader = npy_read
		elif filetype == 'hdf' or filetype=='hdf5':
			reader = hdf_read
		elif filetype == 'nc':
			reader = nc_read
		else:
			raise Exception(f"filetype '{filetype}' id not currently supported for reading files.\n please use a different filetype for output, or add functionality for this filetype")

		check_file_exists(format_output_filepath_views(output_filepath, views[0]))
		X,Y = reader(format_output_filepath_views(output_filepath, views[0]), dataset_name).shape 
		labels = np.zeros((X,Y,len(views)))
		for v, view in enumerate(tqdm(views, "Loading Prior Label File(s)")):
			label_view_filepath = format_output_filepath_views(output_filepath, view)
			check_file_exists(label_view_filepath)
			labels[:,:,v] = reader(label_view_filepath, dataset_name)

		return labels, scene_attributes
