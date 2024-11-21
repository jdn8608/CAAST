import numpy as np
import h5py as h5
import xarray as xr
import datetime

def save_labels(data, scene_labels_dict, output_filepath, dataset_name):
		print(f"{datetime.datetime.now()}: labels saved to {output_filepath}")
		filetype = output_filepath.split('.')[-1]
		if scene_labels_dict:
			scene_attributes = {label: combo_box.currentText() for label, combo_box in scene_labels_dict.items()}
		else:
			scene_attributes=None

		if filetype == 'npy':
			npy_read_write(True, output_filepath, data=data, scene_attrs=scene_attributes)
		elif filetype == 'hdf' or filetype=='hdf5':
			hdf_read_write(True, output_filepath, dataset_name, data=data, scene_attrs=scene_attributes)
		elif filetype == 'nc':
			nc_read_write(True, output_filepath, dataset_name, data=data, scene_attrs=scene_attributes)
		else:
			raise Exception(f"filetype '{filetype}' id not currently supported for saving files.\n please use a different filetype for output, or add functionality for this filetype")

def npy_read_write(write, output_filepath, data=None, scene_attrs=None):
	if write:
		np.save(output_filepath, data)
		if scene_attrs:
			np.save(output_filepath.split('.')[0]+'_scenelabels.npy', scene_attrs)
	else:
		data = np.load(output_filepath, allow_pickle=True)
		if scene_attrs:
			attributes = np.load(output_filepath.split('.')[0]+'_scenelabels.npy', allow_pickle=True)
		else:
			attributes = None
		print(attributes)
		return data, attributes

def nc_read_write(write, output_filepath, dataset_name, data=None, scene_attrs=None):
	if write:
		da = xr.DataArray(
			data,
		)
		if scene_attrs:
			ds = xr.Dataset({dataset_name: da}, attrs=scene_attrs)
		else:
			ds = xr.Dataset({dataset_name:da})
		ds.to_netcdf(output_filepath)
	else:
		ds = xr.open_dataset(output_filepath)
		data = ds[dataset_name].values  # Assuming "labels" is the dataset name
		if scene_attrs:
			attributes = ds.attrs  # xarray stores attributes in the .attrs dictionary
		else:
			attributes = None
		ds.close()

		print(attributes)
		return data, attributes

def hdf_read_write(write, output_filepath, dataset_name, data=None, scene_attrs=None):
	if write:
		out_file = h5.File(output_filepath, "w")
		h5_dataset = out_file.create_dataset(dataset_name, data=data)
		if scene_attrs:
			for key, value in scene_attrs.items():
				h5_dataset.attrs[key] = value
		out_file.close()
	else:
		h5_dataset = h5.File(output_filepath, "r") 
		data = h5_dataset[dataset_name][:]
		if scene_attrs:
			print(output_filepath.split('.')[0]+'_scenelabels.npy')
			attributes = {key: h5_dataset[dataset_name].attrs[key] for key in h5_dataset[dataset_name].attrs}
		else:
			attributes = None
		h5_dataset.close()
		print(attributes)
		return data, attributes	

def read_labels(output_filepath, dataset_name, scene_attrs=False):
		#TODO : chcek that scene labels file exists
		filetype = output_filepath.split('.')[-1]
		if filetype == 'npy':
			return npy_read_write(False, output_filepath, dataset_name, scene_attrs=scene_attrs)
		elif filetype == 'hdf' or filetype=='hdf5':
			return hdf_read_write(False, output_filepath, dataset_name, scene_attrs=scene_attrs)
		elif filetype == 'nc':
			return nc_read_write(False, output_filepath, dataset_name, scene_attrs=scene_attrs)
		else:
			raise Exception(f"filetype '{filetype}' id not currently supported for reading files.\n please use a different filetype for output, or add functionality for this filetype")
