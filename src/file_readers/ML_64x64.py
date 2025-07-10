import glob
import os
import time
import math

import h5py as h5
import numpy as np
import dask.array as da
from tqdm import tqdm

from util.LayerType import LayerType


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
        r for r in glob.glob(os.path.join(parent_dir, search))
        if view in os.path.basename(r)
    ]

    # If there is more than one file found, throw an Exception
    if len(search_result_files) != 1:
        raise Exception(
            "A single file was not found. \n"
            "Please refine the search key found in the config file.\n"
            f"The results of the search was:\n {search_result_files}")

    return search_result_files[0]


def read(parent_dir, search, views, config=None, lazy=False):
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
    add_nan_mask = config["create_nan_mask"]
    add_dtt = config["add_dtt"]
    add_sid = config["add_surface_id"]
    add_geom = config["add_sun_view_geometry"]

    # Get the filepath
    filepath = parent_dir

    start_time = time.time()
    hdf_file = h5.File(filepath, 'r')

    bands_to_use = np.array([1, 2, 3, 4, 20, 26, 31], np.float32)
    rad_index = []
    all_band_nums = np.array(hdf_file["BAND_NUMS"], dtype=np.float64)
    for b in bands_to_use:
        rad_index.append(np.where(all_band_nums == b)[0][0])

    if lazy:
        all_rad = da.from_array(hdf_file["MOD02_RAD"], chunks="auto")
        all_rad = da.swapaxes(da.swapaxes(all_rad, 0, 1), 1, 2)[..., np.newaxis]
        all_rad = all_rad[..., rad_index, :]
        ml_probs = da.from_array(hdf_file["ML_PROBS"], chunks="auto")
        ml_masks = da.from_array(hdf_file["ML_MASKS"], chunks="auto")
    else:
        all_rad = np.swapaxes(
            np.swapaxes(np.array(hdf_file["MOD02_RAD"]), 0, 1), 1,
            2)[..., np.newaxis]
        all_rad = all_rad[..., rad_index, :]
        ml_probs = np.array(hdf_file["ML_PROBS"])
        ml_masks = np.array(hdf_file["ML_MASKS"])

    # Create the returnable dictionary
    data_layer_dict = {}

    if lazy:
        data_layer_dict["MOD35"] = (
            LayerType.CLOUD_MASK,
            da.from_array(hdf_file["MOD35"], chunks="auto")[..., np.newaxis])
        rccm = da.from_array(hdf_file["RCCM"], chunks="auto")[..., np.newaxis]
    else:
        data_layer_dict["MOD35"] = (
            LayerType.CLOUD_MASK,
            np.array(hdf_file["MOD35"])[..., np.newaxis])
        rccm = np.array(hdf_file["RCCM"])[..., np.newaxis]
    rccm[rccm == 1] = 3

    def normalize(band):
        return (band - np.min(band)) / (np.max(band) - np.min(band))

    data_layer_dict["RCCM"] = (LayerType.CLOUD_MASK, rccm)
    for i, b in enumerate(bands_to_use):
        data_layer_dict[f"Band {b}"] = (LayerType.GRAY_BAND, all_rad[..., i, :])

    if lazy:
        rgb = da.from_array(hdf_file["TRUE_COLOR"], chunks="auto")[..., np.newaxis]
    else:
        rgb = np.array(hdf_file["TRUE_COLOR"])[..., np.newaxis]
    data_layer_dict["RGB"] = (LayerType.RGB, rgb)

    for i, name in enumerate(["MODIS E100", "MODIS E250", "MISR E100", "MISR E250"]):
        ml_mask_temp = ml_masks[i][..., np.newaxis]
        ml_mask_temp[ml_mask_temp == 1] = 3
        data_layer_dict[f"{name} MASK"] = (LayerType.CLOUD_MASK, ml_mask_temp)

    x, y = tuple(hdf_file["COORDS"])
    x = int(x) - 1
    y = int(y) - 1
    dy, dx = 63, 63
    width = 5
    data_layer_dict[f"Bounding Box"] = (
        LayerType.SHAPE,
        np.array([
            [x - math.ceil(width / 2), y - math.ceil(width / 2)],
            [x - math.ceil(width / 2), y + dy + width],
            [x + dx + width, y + dy + width],
            [x + dx + width, y - math.ceil(width / 2)],
        ]))

    shape = all_rad.shape
    shape = (shape[0], shape[1], shape[2], shape[3])

    if not lazy:
        hdf_file.close()

    print("DATA RETURNED")
    return data_layer_dict, filepath, shape
