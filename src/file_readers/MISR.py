import xarray as xr
import numpy as np

from util.LayerType import LayerType

X_DIM = 192
Y_DIM = 192
MAX_CHANNELS = 1

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

def read(parent_dir, search, views, config=None):
    """Finds MAIA files and reads in required data for the tool

    Args:
        parent_dir  : the root (parent) directory to search to find files within
        search      : a comprehensive string to search for files with a pattern... '*' symbols are wildcards.
        views       : a list of strings to represent the views for the instrument. If the instrument is not
                    a multi-angle instrument, the list should be of lenght 1.
        config      : a dictionary of config options that may be useful for your data ingestion for a instrument
                    data.

    Returns:
        a "data" dictionary : The keys are the name of the layers to add into the tool. The values are tuple,
                            where entry [0] is a LayerType (see file_readers/LayerType.py) that indicates how
                            this data layer will be used... entry [1] is a NumPy array of the data layer to
                            be added.
     - a string             : that represents the filename of the output file. Should contain sub-string
                            '<view>' if there are multiple views so that each view can be saved out seperately
                            by replacing this sub-string when file writing.
     - a tuple              : that represents the NumPy shape for layers that will be added as image layers (not
                            labels)
    """
    # Get additional attributes from config file
    bands_to_get = config["bands"]
    add_cloud_mask = config["add_cloud_mask"]
    thresholds = config["thresholds"]

    num_of_channels = 1
    band_names = ['red']

    # Intialize NumPy arrays
    band_data = np.zeros((Y_DIM, X_DIM, num_of_channels, len(views)))
    if add_cloud_mask:
        cloud_masks = np.zeros((Y_DIM, X_DIM, len(views)))

    # Load MISR data file
    misr_data = xr.load_dataset(parent_dir+search)

    # Loop through all views
    for i, view in enumerate(views):
        # Get the band data
        brf = misr_data.sel(camera=view).brf.data
        band_data[:,:,0,i] = brf

        # Generate a rough cloud mask
        if add_cloud_mask:
            threshold = thresholds[i]
            mask = np.zeros((Y_DIM, X_DIM))
            mask[brf > threshold] = 1
            cloud_masks[:,:,i] = mask

    # Create the returnable dictionary
    data_layer_dict = {}
    # Add the band data to the dict, one band at a time
    for i, name in enumerate(band_names):
        data_layer_dict[str(name)] = (LayerType.GRAY_BAND, band_data[...,
                                                                     i, :])
    # Get the band_data shape and cast as a list if a dim needs to be edited
    shape = list(band_data.shape)

    # Add the cloud mask to the dict
    if add_cloud_mask:
        data_layer_dict["Cloud Mask"] = (LayerType.CLOUD_MASK, cloud_masks)

    # Reset shape to an immutable tuple
    shape = tuple(shape)

    output_file = '/cloud_mask_<view>.hdf'
    return data_layer_dict, output_file, shape
