import glob
import os
import h5py as h5
import numpy as np
from tqdm import tqdm

X_DIM = 360
Y_DIM = 480
# will need to fix once we have the other channels for MAIA
MAX_CHANNELS = 6


def find_file(parent_dir, search, view=''):
    """find the file to open within a directory based on a search string

    Args:
        parent_dir: the root (parent) directory to search for files within
        search: a comprehensive string to search for files with a pattern... '*' symbols are wildcards.
            The string should only return either 1 or <number of views> files.
        view: a string to seperate filename strings for a specific view from others. This is wanted when,
            the search string returns multiple files for various views. If not needed, the default value 
            is sufficient.

    Returns:
        a filepath string to be opened for ingesting data for the given view

    Exception:
        An exception is thrown if more than one file is found from the search string and view string

    """

    # Search for a file based on the search string and filter by the view string
    search_result_files = [
        r for r in glob.glob(f'{parent_dir}/{search}') if view in r
    ]

    # If there is more than one file found, throw an Exception
    if len(search_result_files) != 1:
        raise Exception(
            "A single file was not found. \n"
            "Please refine the search key found in the config file.\n"
            f"The results of the search was:\n {search_result_files}")

    return search_result_files[0]


def read_single_view(parent_dir,
                     search,
                     view,
                     bands_to_get='ALL',
                     get_cloud_mask=False,
                     config=None):

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
    band_data = np.zeros((Y_DIM, X_DIM, num_of_data_channels + 1, len(view)))

    if get_cloud_mask:
        cloud_masks = np.zeros((Y_DIM, X_DIM, len(view)))

    for i, v in enumerate(view):
        # Find the file
        filepath = find_file(parent_dir, search, view=v)
        print(filepath)

        # open file

        #band_data[:,:,:,i] = get_bands()

        #if get_cloud_mask:
        #    cloud_masks[:,:,i] = get_cloud_mask()

        #if load_nan_mask:
        #    = get_nan_vals()

    # Add to dict
    quit()
    return multiangle_data, bands, cloud_masks, path
