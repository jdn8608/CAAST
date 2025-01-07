import glob
import os

import h5py as h5
import numpy as np
from tqdm import tqdm

from file_readers.LayerType import LayerType

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


def get_dtt(hdf_file):
    """Get the Distance to Threshold (DTT) data from the the MAIA file

    Args:
        hdf_file: h5 File object for the current file

    Returns:
        the MAIA observables and their correspondind DTT used within the MAIAcloud mask algorithm,
        each of shape (HEIGHT, WIDTH, number of OBSERVABLES)
    """
    dtt = np.array(hdf_file["cloud_mask_output"]["DTT"])
    dtt_obs = np.array(hdf_file["cloud_mask_output"]["observable_data"])

    # Filter out NaN values within the MAIA product and set to 0
    dtt[dtt < 0] = 0
    dtt_obs[dtt_obs < 0] = 0

    return dtt, dtt_obs


def get_sids(hdf_file):
    """Get the Surface Identifier (SID) data from the the MAIA file

    Args:
        hdf_file: h5 File object for the current file

    Returns:
        the MAIA SIDs of shape (HEIGHT, WIDTH)
    """

    sid = np.array(hdf_file['Ancillary']['scene_type_identifier'])

    # Replace NaN values with -1
    sid[sid < 0] = -1

    return sid


def get_view_geometery(hdf_file, attributes=[]):
    """Get the viewing geometery data from the the MAIA file

    Args:
        hdf_file: h5 File object for the current file
        attributes : a list of attribute names in the MAIA file

    Returns:
        the MAIA viewing geometery NumPy array of shape (HEIGHT, WIDTH, len(attributes))
    """

    vg = np.zeros((Y_DIM, X_DIM, len(attributes)))

    for a, attr in enumerate(attributes):
        vg[..., a] = np.array(hdf_file['sun_view_geometry'][attr])

    return vg


def create_nan_mask(band_data):
    """Create a mask indicating where any nan_values are found across the loaded band data.
    Note this is subjective to the data loaded... if there are nans in bands not loaded, this
    will not be indicated by this mask.

    Args:
        band_data: a NumPy array of the MAIA band data loaded

    Returns:
        a NumPy array of shape (HEIGHT,WIDTH) indicating where nan values are found
        an updated band_data, where NaN values are replaced with a value of 0.
    """
    # MAIA uses -999, -998, or NaN as values indicating no data present
    # Each value indicates different out of bound conditions
    # For the purpose of the NaN mask, they are all considered the same
    nan_mask = (band_data == -999.0) | (band_data
                                        == -998.0) | (np.isnan(band_data))
    band_data[nan_mask] = 0
    nan_mask = np.any(nan_mask, axis=2)
    return nan_mask, band_data


def read(parent_dir,
         search,
         views,
         bands_to_get='ALL',
         add_cloud_mask=False,
         add_nan_mask=True,
         add_dtt=True,
         add_sid=True,
         add_geom=True,
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
    band_data = np.zeros((Y_DIM, X_DIM, num_of_channels, len(views)))
    if add_cloud_mask:
        cloud_masks = np.zeros((Y_DIM, X_DIM, len(views)))
    if add_nan_mask:
        nan_masks = np.zeros((Y_DIM, X_DIM, len(views)))
    if add_dtt:
        obs_names = [
            "R Band 6", "R Band 9", "R Band 13", "NDVI", "NDSI",
            "Whiteness Index", "SVI"
        ]
        num_of_observables = len(obs_names)

        dtt = np.zeros((Y_DIM, X_DIM, num_of_observables, len(views)))
        dtt_obs = np.zeros((Y_DIM, X_DIM, num_of_observables, len(views)))
    if add_sid:
        sid = np.zeros((Y_DIM, X_DIM, len(views)))
    if add_geom:
        view_geometery_names = [
            'solar_azimuth_angle', 'solar_zenith_angle',
            'viewing_azimuth_angle', 'viewing_zenith_angle'
        ]
        view_geometery = np.zeros(
            (Y_DIM, X_DIM, len(view_geometery_names), len(views)))

    # Loop through all views
    for i, view in enumerate(views):
        # Find the file
        filepath = find_file(parent_dir, search, view=view)

        # Open file
        hdf_file = h5.File(filepath, 'r')

        # If bands_to_get is 'ALL', on first file pass, grab the band names
        if band_names is None:
            band_names = np.array(list(hdf_file['Reflectance'].keys()))

        # Get the band data
        band_data[..., i] = get_bands(hdf_file, band_names, num_of_channels)
        # Create a mask indicating where NaNs are found
        if add_nan_mask:
            nan_masks[..., i], band_data[...,
                                         i] = create_nan_mask(band_data[...,
                                                                        i])
        # Get DTT and Observables from the MAIA file
        if add_dtt:
            dtt[..., i], dtt_obs[..., i] = get_dtt(hdf_file)

        # Get the Surface IDS from the MAIA file
        if add_sid:
            sid[..., i] = get_sids(hdf_file)

        # Get the Sun-View Geometery from the MAIA file
        if add_geom:
            view_geometery[...,
                           i] = get_view_geometery(hdf_file,
                                                   view_geometery_names)

        # Get the cloud mask
        if add_cloud_mask:
            cloud_masks[..., i] = get_cloud_mask(hdf_file)

        # Close the hdf file to force garbage collection and limit memory needs
        # Also prevents h5py File load errors
        hdf_file.close()

    # Create the returnable dictionary
    data_layer_dict = {}
    # Add the band data to the dict, one band at a time
    for i, name in enumerate(band_names):
        data_layer_dict[str(name)] = (LayerType.GRAY_BAND, band_data[...,
                                                                     i, :])
    # Get the band_data shape and cast as a list if a dim needs to be edited
    shape = list(band_data.shape)

    if add_dtt:
        shape[2] += 2 * len(obs_names)
        for i, name in enumerate(obs_names):
            data_layer_dict[str(name)] = (LayerType.OBSERVABLE, dtt_obs[...,
                                                                        i, :])
            data_layer_dict['DTT ' + str(name)] = (LayerType.DTT, dtt[...,
                                                                      i, :])

    if add_geom:
        shape[2] += len(view_geometery_names)
        for a, attr in enumerate(view_geometery_names):
            data_layer_dict[attr] = (LayerType.VIEW_GEO, view_geometery[...,
                                                                        a, :])

    # Add the nan mask to the dict
    if add_nan_mask:
        data_layer_dict["NaN Mask"] = (LayerType.NAN_MASK, nan_masks)

    if add_sid:
        data_layer_dict["Surface IDS"] = (LayerType.SURFACE_ID, sid)

    # Add the MAIA cloud mask to the dict
    if add_cloud_mask:
        data_layer_dict["Cloud Mask"] = (LayerType.CLOUD_MASK, cloud_masks)

    # Reset shape to an immutable tuple
    shape = tuple(shape)

    return data_layer_dict, filepath.replace(view, '<view>'), shape
