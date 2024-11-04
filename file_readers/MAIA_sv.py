import glob
import h5py as h5 
import numpy as np
from tqdm import tqdm


def read(parent_dir, config=None):
	search = config['filename_search_string']
	view = config['view']

	search_result_files = [ r for r in glob.glob(f'{parent_dir}/{search}') if view in r]
	if len(search_result_files) != 1:
		raise Exception(f"A single file was not found. \n please refine the search key found in the config file.\n The results of the search was:\n {search_result_files}")

	
	hdf_file = h5.File(search_result_files[0], 'r')
	if config["bands"] == 'ALL':
		bands = np.array(list(hdf_file['Reflectance'].keys()))
	else:	
		bands = np.empty((len(config["bands"])), dtype='S7') 
		for i, band_num in enumerate(config["bands"]):
			if band_num > 9:
				bands[i] = f'band_{band_num}'
			else:
				bands[i] = f'band_0{band_num}' 
		
	num_of_data_channels = bands.shape[0]
	load_cloud_mask = False

	data = np.zeros((480,360,num_of_data_channels+1))
	for i, band in enumerate(bands):
		data[:,:,i] = np.array(hdf_file['Reflectance'][band])

	if config['load_labels'] == 'cloud mask':
		cloud_mask = np.array(hdf_file['cloud_mask_output']['final_cloud_mask'])
		bands = np.concatenate((bands, ['MAIA Cloud Mask']))
	else:
		cloud_mask = None
		 		
	# TODO: SIMPLIFY CLOUD MASK LOGIC BY RETURNING MASK AS SEPERATE OBJECT
	# TODO: ADD APRIORI LOADING
	
	return data, bands, cloud_mask, search_result_files[0]

