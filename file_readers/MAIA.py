import glob
import os
import h5py as h5
import numpy as np
from tqdm import tqdm

X_DIM = 360
Y_DIM = 480
# will need to fix once we have the other channels for MAIA
MAX_CHANNELS = 6


def read_single_view(parent_dir,
                     search,
                     view,
                     bands_to_get='ALL',
                     get_cloud_mask=False,
                     config=None):

	search_result_files = [
	    r for r in glob.glob(f'{parent_dir}/{search}') if view in r
	]
	if len(search_result_files) != 1:
		raise Exception(
		    f"A single file was not found. \n please refine the search key found in the config file.\n The results of the search was:\n {search_result_files}"
		)

	hdf_file = h5.File(search_result_files[0], 'r')
	if bands_to_get[0].upper() == 'ALL':
		bands = np.array(list(hdf_file['Reflectance'].keys()))
	else:
		bands = np.empty((len(bands_to_get)), dtype='S7')
		for i, band_num in enumerate(bands_to_get):
			if band_num > 9:
				bands[i] = f'band_{band_num}'
			else:
				bands[i] = f'band_0{band_num}'

	num_of_data_channels = bands.shape[0]
	data = np.zeros((Y_DIM, X_DIM, num_of_data_channels + 1))
	for i, band in enumerate(bands):
		data[:, :, i] = np.array(hdf_file['Reflectance'][band])

	# add NAN mask to data cube
	bands = np.concatenate((bands, ['No Retrieval']))
	NA_MASK = (data == -999.0) | (data == -998.0) | (np.isnan(data))
	data[NA_MASK] = 0
	data[:, :, -1] = np.any(NA_MASK, axis=2)

	if get_cloud_mask.upper() == 'CLOUD MASK':
		cloud_mask = np.array(
		    hdf_file['cloud_mask_output']['final_cloud_mask'])
		bands = np.concatenate((bands, ['MAIA Cloud Mask']))
		cloud_mask[cloud_mask == 3] = -1
	else:
		cloud_mask = None

	# TODO: ADD APRIORI LOADING

	return data, bands, cloud_mask, search_result_files[0].replace(
	    view, '<view>')


def read(parent_dir,
         search,
         view,
         bands_to_get='ALL',
         get_cloud_mask=False,
         config=None):

	if bands_to_get[0].upper() == 'ALL':
		num_of_data_channels = MAX_CHANNELS
	else:
		num_of_data_channels = len(bands_to_get)

	multiangle_data = np.zeros(
	    (Y_DIM, X_DIM, num_of_data_channels + 1, len(view)))
	cloud_masks = np.zeros((Y_DIM, X_DIM, len(view)))

	for i, v in enumerate(view):
		multiangle_data[:, :, :,
		                i], bands, cloud_masks[:, :,
		                                       i], path = read_single_view(
		                                           parent_dir,
		                                           search=search,
		                                           view=v,
		                                           bands_to_get=bands_to_get,
		                                           get_cloud_mask=get_cloud_mask
		                                       )

	return multiangle_data, bands, cloud_masks, path
