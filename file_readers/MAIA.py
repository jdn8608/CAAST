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
    """Find the file to open within a directory based on a search string

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


def format_band_names(bands_to_get):
    """Format band numbers to MAIA formated band name strings. This will allow for the
    names to be used to get the appropriate band data when ingested 

    Args:
        bands_to_get: a list of band numbers to retrieve from the MAIA file(s). The entries
            in the list can be of type int or str

    Returns:
        a list of strings of MAIA formatted band names:w
    """
    band_names = np.empty((len(bands_to_get)), dtype='S7')
    for i, band_num in enumerate(bands_to_get):

        # Format the band number to a string if an int
        if isinstance(band_num, str):
            band_num = int(band_num)

        # MAIA band naming convention formatting
        if band_num > 9:
            band_names[i] = f'band_{band_num}'
        else:
            band_names[i] = f'band_0{band_num}'

    return band_names


def get_bands(hdf_file, band_names, num_of_channels):
    """Get the band data imagery from the MAIA hdf file

    Args:
        hdf_file: h5 File object for the current file
        band_names: a list of MAIA formatted band name strings
        num_of_channels: an int representing the number of channels to ingest

    Returns:
        a NumPy array of the MAIA band imagery data of shape (HEIGHT,WIDTH,num_of_channels)
    """
    band_data = np.zeros((Y_DIM, X_DIM, num_of_channels))

    for i, name in enumerate(band_names):
        band_data[:, :, i] = np.array(hdf_file['Reflectance'][name])

    return band_data


def get_cloud_mask(hdf_file):
    """Get the cloud mask from the MAIA hdf file

    Args:
        hdf_file: h5 File object for the current file

    Returns:
        the MAIA cloud mask of shape (HEIGHT, WIDTH) with NaN values replaced with the value 3
    """
    # Open and load the cloud mask
    cloud_mask = np.array(hdf_file['cloud_mask_output']['final_cloud_mask'])
    # Convet NaN mask values (3) to -1 for the purpose of colormap formatting
    cloud_mask[cloud_mask == 3] = -1
    return cloud_mask


def create_nan_mask(band_data):
    """Create a mask indicating where any nan_values are found across the loaded band data.
    Note this is subjective to the data loaded... if there are nans in bands not loaded, this
    will not be indicated by this mask.

    Args:
        band_data: a NumPy array of the MAIA band data loaded

    Returns:
        a NumPy array of shape (HEIGHT,WIDTH) indicating where nan values are found
    """
    # MAIA uses -999, -998, or NaN as values indicating no data present
    # Each value indicates different out of bound conditions
    # For the purpose of the NaN mask, they are all considered the same
    nan_mask = (band_data == -999.0) | (band_data
                                        == -998.0) | (np.isnan(band_data))
    return nan_mask


def read(parent_dir,
         search,
         view,
         bands_to_get='ALL',
         add_cloud_mask=False,
         add_nan_mask=True,
         config=None):
    """Finds MAIA files and reads in required data for the tool

    Args:
        parent_dir: the root (parent) directory to search for files within
        search: a comprehensive string to search for files with a pattern... '*' symbols are wildcards.
           See find_file() for use case and details.
        views: a list of strings indicating the views to load. These sub-strings should be present in the filename
        bands_to_get: a list of numbers (as ints or strs) indicating the bands to open from the MAIA file(s).
            A value of 'ALL' will load all bands found within the file(s).
        add_cloud_mask: a binary to indicate the call of cloud mask loading.
        add_nan_mask: a binary to indicate the call of creating a mask where nan MAIA values are found.

    Returns:
        a dictionairy, where the keys are the name of the layer data for the tool/visualization, and the values
        are tuples of (layer type, NumPy data array).

        See TBD for possible layer type values, and the implications on the tool.
    """

    # Check what bands to load and how many bands
    if bands_to_get[0].upper() == 'ALL':
        num_of_channels = MAX_CHANNELS
        band_names = None
    else:
        num_of_channels = len(bands_to_get)
        band_names = format_band_names(bands_to_get)

    # Intialize NumPy arrays
    band_data = np.zeros((Y_DIM, X_DIM, num_of_channels, len(view)))
    if add_cloud_mask:
        cloud_masks = np.zeros((Y_DIM, X_DIM, len(view)))
    if add_nan_mask:
        nan_masks = np.zeros((Y_DIM, X_DIM, len(view)))

    # Loop through all views
    for i, v in enumerate(view):
        # Find the file
        filepath = find_file(parent_dir, search, view=v)

        # Open file
        hdf_file = h5.File(filepath, 'r')

        # If bands_to_get is 'ALL', on first file pass, grab the band names
        if band_names is None:
            band_names = np.array(list(hdf_file['Reflectance'].keys()))

        # Get the band data
        band_data[..., i] = get_bands(hdf_file, band_names, num_of_channels)

        # Get the cloud mask
        if add_cloud_mask:
            cloud_masks[..., i] = get_cloud_mask(hdf_file)

        # Create a mask indicating where NaNs are found
        if add_nan_mask:
            nan_mask[..., i] = create_nan_mask()

        # Close the hdf file to force garbage collection and limit memory needs
        # Also prevents h5py File load errors
        hdf_file.close()

    # Create dict
    quit()
    return multiangle_data, bands, cloud_masks, path
