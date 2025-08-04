import glob
import os
from pathlib import Path

import h5py as h5
import numpy as np
from tqdm import tqdm

from util.LayerType import LayerType

X_DIM = 360
Y_DIM = 480
# will need to fix once we have the other channels for MAIA
MAX_CHANNELS = 6

# TOOD: Delete this and connected logic for MAIA file format later
VIEW_ORDER = ["DA", "CA", "BA", "AA", "AN", "AF", "BF", "CF", "DF"]
VIEW_ANGLES = {
    "DA": -70.0,
    "CA": -60.0,
    "BA": -45.6,
    "AA": -26.1,
    "AN": 0.0,
    "AF": 26.1,
    "BF": 45.6,
    "CF": 60.0,
    "DF": 70.0,
}
VIEW_INDEX = {view: i for i, view in enumerate(VIEW_ORDER)}


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
        band_data[..., i] = np.array(hdf_file['Reflectance'][name])
    band_data[band_data < 0] = 0

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
    cloud_mask[cloud_mask < -100] = -1
    cloud_mask[cloud_mask == 3] = -1
    cloud_mask[cloud_mask == 2] = -1
    cloud_mask[cloud_mask == 1] = 3  # temp for 4 color colormap
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

    dtt[dtt < -124] = -1
    dtt_obs[dtt_obs < -124] = -1

    dtt[np.isnan(dtt)] = -1
    dtt_obs[np.isnan(dtt_obs)] = -1

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


def get_view_geometry(hdf_file, attributes=[]):
    """Get the viewing geometry data from the the MAIA file

    Args:
        hdf_file: h5 File object for the current file
        attributes : a list of attribute names in the MAIA file

    Returns:
        the MAIA viewing geometry NumPy array of shape (HEIGHT, WIDTH, len(attributes))
    """

    vg = np.zeros((Y_DIM, X_DIM, len(attributes)))

    for a, attr in enumerate(attributes):
        vg[..., a] = np.array(hdf_file['sun_view_geometry'][attr])

    # replace NaN values
    vg[vg < 0] = 0

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


# From Guangyu Zhao
def bytescale(data, cmin=None, cmax=None, high=255, low=0):
    """
    Byte scales an array (image).

    Byte scaling means converting the input image to uint8 dtype and scaling
    the range to ``(low, high)`` (default 0-255).
    If the input image already has dtype uint8, no scaling is done.

    Parameters
    ----------
    data : ndarray
        PIL image data array.
    cmin : scalar, optional
        Bias scaling of small values. Default is ``data.min()``.
    cmax : scalar, optional
        Bias scaling of large values. Default is ``data.max()``.
    high : scalar, optional
        Scale max value to `high`.  Default is 255.
    low : scalar, optional
        Scale min value to `low`.  Default is 0.

    Returns
    -------
    img_array : uint8 ndarray
        The byte-scaled array.

    Examples
    --------
    >>> img = array([[ 91.06794177,   3.39058326,  84.4221549 ],
                     [ 73.88003259,  80.91433048,   4.88878881],
                     [ 51.53875334,  34.45808177,  27.5873488 ]])
    >>> bytescale(img)
    array([[255,   0, 236],
           [205, 225,   4],
           [140,  90,  70]], dtype=uint8)
    >>> bytescale(img, high=200, low=100)
    array([[200, 100, 192],
           [180, 188, 102],
           [155, 135, 128]], dtype=uint8)
    >>> bytescale(img, cmin=0, cmax=255)
    array([[91,  3, 84],
           [74, 81,  5],
           [52, 34, 28]], dtype=uint8)

    """
    if data.dtype == np.uint8:
        return data

    if high < low:
        raise ValueError("`high` should be larger than `low`.")

    if cmin is None:
        cmin = np.nanmin(data.flatten())
    if cmax is None:
        cmax = np.nanmax(data.flatten())

    cscale = cmax - cmin
    if cscale < 0:
        raise ValueError("`cmax` should be larger than `cmin`.")
    elif cscale == 0:
        cscale = 1

    scale = float(high - low) / cscale
    bytedata = (data * 1.0 - cmin) * scale + 0.4999
    bytedata[bytedata > high] = high
    bytedata[bytedata < 0] = 0
    return np.asarray(bytedata, dtype=np.uint8) + np.uint8(low)


# From Guangyu Zhao
def get_enhanced_RGB(RGB):
    """
    Convert RGB BRFs to 8-bit color space [0,255]
    """

    def scale_image(image):
        along_track = image.shape[0]
        cross_track = image.shape[1]

        x = np.array([0, 30, 60, 120, 190, 255], dtype=np.uint8)
        y = np.array([0, 110, 160, 210, 240, 255], dtype=np.uint8)

        scaled = np.zeros((along_track, cross_track), dtype=np.uint8)
        for i in range(len(x) - 1):
            x1 = x[i]
            x2 = x[i + 1]
            y1 = y[i]
            y2 = y[i + 1]
            m = (y2 - y1) / float(x2 - x1)
            b = y2 - (m * x2)
            mask = ((image >= x1) & (image < x2))
            scaled = scaled + mask * np.asarray(m * image + b, dtype=np.uint8)

        mask = image >= x2
        scaled = scaled + (mask * 255)
        return scaled

    enhanced_RGB = np.zeros_like(RGB, dtype=np.uint8)
    for i in range(3):
        enhanced_RGB[:, :, i] = scale_image(bytescale(RGB[:, :, i]))
    return enhanced_RGB


def create_true_color(hdf_file):
    ref06 = hdf_file['Reflectance/band_06'][()]
    ref05 = hdf_file['Reflectance/band_05'][()]
    ref04 = hdf_file['Reflectance/band_04'][()]
    ref06[ref06 < 0] = np.nan
    ref05[ref05 < 0] = np.nan
    ref04[ref04 < 0] = np.nan
    RGB = np.dstack((((ref06)), \
        ((ref05)),((ref04))))

    RGB[RGB == -999] = np.nan

    # Adding code to nan out columns with missing any rgb data
    nan_mask = np.isnan(RGB).any(axis=2)
    RGB[nan_mask] = np.nan

    RGB = get_enhanced_RGB(RGB)
    return RGB


def get_aerosol_data_from_file(file_path, shape):
    """Read Total AODs from a MAIA aerosol file"""
    import netCDF4 as nc

    # Load NetCDF data
    with nc.Dataset(file_path, 'r') as ds:
        total_AOD = ds.groups['Aerosol_Optical_Depth'].variables[
            'Total_AOD'][:]
        data = total_AOD.data.copy()
        data[total_AOD.mask] = -1  # Replace masked values with -1

        # Reshape and label
        O, W, H = total_AOD.shape
        formatted = np.transpose(data, axes=(2, 1, 0))  # -> (H, W, O)
        names = [f"Total_AOD: {wl} nm" for wl in ds.getncattr('wavelengths')]

    # Expand to multiview dim and pad height width
    expanded = np.repeat(formatted[..., np.newaxis], shape[0], axis=-1)

    return pad(expanded, shape, T_x=-4, T_y=-8).transpose(3, 0, 1, 2), names


def pad(arr, shape_to_pad, T_y=0, T_x=0):
    """Add padding on the first two dims (height, width) to match ``shape_to_pad``."""

    V, H, W = shape_to_pad
    # Calculate padding needed for each dimension
    pad_height = H - arr.shape[0]
    pad_width = W - arr.shape[1]

    # Compute symmetric padding (before, after)
    pad_top = pad_height // 2 + T_y
    pad_bottom = pad_height - pad_top

    pad_left = pad_width // 2 + T_x
    pad_right = pad_width - pad_left
    # Apply padding
    padded_arr = np.pad(arr,
                        pad_width=((pad_top, pad_bottom),
                                   (pad_left, pad_right), (0, 0), (0, 0)),
                        mode='constant',
                        constant_values=-1)
    return padded_arr


def read(files, config=None):
    """Read MAIA files and return data for the tool

    Args:
        files      : list of filepaths (absolute or relative to ``parent_dir``)
        config     : optional configuration dictionary

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
     - a list               : the view names extracted from the filenames
     - a list               : the corresponding viewing angles
    """

    # Sort files by view camera
    def extract_view(file_path):
        parts = Path(file_path).stem.split("_")
        return VIEW_INDEX.get(
            parts[4], float('inf'))  # fallback to inf if view not found

    files = sorted(files, key=extract_view)

    # Normalize file paths and separate by type
    aerosol_files = [f for f in files if "_AER_" in f.upper()]
    mask_files = [f for f in files if "MCM_" in f.upper()]

    # Determine views and angles from cloud mask filenames
    views = []
    angles = []
    for f in mask_files:
        base = os.path.basename(f)
        view = None
        for v in VIEW_ORDER:
            if f"_{v}_" in base:
                view = v
                break
        if view is None:
            view = os.path.splitext(base)[0]
        views.append(view)
        angles.append(VIEW_ANGLES.get(view, np.nan))

    # Get additional attributes from config file
    bands_to_get = config["bands"]
    add_cloud_mask = config["add_cloud_mask"]
    add_nan_mask = config["create_nan_mask"]
    add_dtt = config["add_dtt"]
    add_sid = config["add_surface_id"]
    add_geom = config["add_sun_view_geometry"]
    add_true_color = True

    # Check what bands to load and how many bands
    if bands_to_get[0].upper() == 'ALL':
        num_of_channels = MAX_CHANNELS
        band_names = None
    else:
        num_of_channels = len(bands_to_get)
        band_names = format_band_names(bands_to_get)

    # Grab shape of V, H, W
    image_shape = (len(views), Y_DIM, X_DIM)

    # Initialize NumPy arrays for data attributes
    band_data = np.zeros((len(views), Y_DIM, X_DIM, num_of_channels))
    if add_true_color:
        rgb = np.zeros((len(views), Y_DIM, X_DIM, 3))
    if add_cloud_mask:
        cloud_masks = np.zeros((len(views), Y_DIM, X_DIM))
    if add_nan_mask:
        nan_masks = np.zeros((len(views), Y_DIM, X_DIM))
    if add_dtt:
        obs_names = ["WI", "NDVI", "NDSI", "visRef", "nirRef", "SVI", "Cirrus"]
        num_of_observables = len(obs_names)

        dtt = np.zeros((len(views), Y_DIM, X_DIM, num_of_observables))
        dtt_obs = np.zeros((len(views), Y_DIM, X_DIM, num_of_observables))
    if add_sid:
        sid = np.zeros((len(views), Y_DIM, X_DIM))
    if add_geom:
        view_geometry_names = [
            'solar_azimuth_angle', 'solar_zenith_angle',
            'viewing_azimuth_angle', 'viewing_zenith_angle'
        ]
        view_geometry = np.zeros(
            (len(views), Y_DIM, X_DIM, len(view_geometry_names)))

    activations_needed = np.zeros(len(views))
    activation_values_arr = None
    fill_val_2_list = np.zeros(len(views))
    fill_val_3_list = np.zeros(len(views))

    # Loop through cloud mask files
    for i, (view, filepath) in enumerate(zip(views, mask_files)):
        hdf_file = h5.File(filepath, 'r')

        # Get MCM ancillary configuration
        # TODO: Open an issue about MCM Proxy data key for number of tests
        number_of_activations_need = hdf_file['Ancillary'][
            'configuration_file'][
                'Min_num_of_activated_testsMin_num_of_activated_tests'][()]
        activation_values = hdf_file['Ancillary']['configuration_file'][
            'activation_values'][()]
        fill_val_2 = hdf_file['Ancillary']['configuration_file']['fill_val_2'][
            ()]
        fill_val_3 = hdf_file['Ancillary']['configuration_file']['fill_val_3'][
            ()]

        activations_needed[i] = number_of_activations_need
        fill_val_2_list[i] = fill_val_2
        fill_val_3_list[i] = fill_val_3
        if activation_values_arr is None:
            activation_values_arr = np.zeros(
                (len(activation_values), len(views)))
        activation_values_arr[:, i] = activation_values

        # If bands_to_get is 'ALL', on first file pass, grab the band names
        if band_names is None:
            band_names = np.array(list(hdf_file['Reflectance'].keys()))

        # Get the band data
        band_data[i] = get_bands(hdf_file, band_names, num_of_channels)

        # Create a true color composite from bands 4 5 6
        if add_true_color:
            rgb[i] = create_true_color(hdf_file)

        # Create a mask indicating where NaNs are found
        if add_nan_mask:
            nan_masks[i], band_data[i] = create_nan_mask(band_data[i])
        # Get DTT and Observables from the MAIA file
        if add_dtt:
            dtt[i], dtt_obs[i] = get_dtt(hdf_file)

        # Get the Surface IDS from the MAIA file
        if add_sid:
            sid[i] = get_sids(hdf_file)

        # Get the Sun-View Geometery from the MAIA file
        if add_geom:
            view_geometry[i] = get_view_geometry(hdf_file, view_geometry_names)

        # Get the cloud mask
        if add_cloud_mask:
            cloud_masks[i] = get_cloud_mask(hdf_file)

        # Close the hdf file to force garbage collection and limit memory needs
        # Also prevents h5py File load errors
        hdf_file.close()

    # Create the returnable dictionary
    data_layer_dict = {}
    # Add the band data to the dict, one band at a time
    for i, name in enumerate(band_names):
        data_layer_dict[str(name)] = (
            LayerType.GRAY_BAND,
            band_data[..., i],
        )

    # Add True Color Composite
    if add_true_color:
        data_layer_dict["True Color"] = (LayerType.RGB, rgb)

    # Add DTT and OBSERVABLES to the dict
    if add_dtt:
        for i, name in enumerate(obs_names):
            data_layer_dict[str(name)] = (
                LayerType.OBSERVABLE,
                dtt_obs[..., i],
            )
            data_layer_dict["DTT " + str(name)] = (
                LayerType.DTT,
                dtt[..., i],
            )

    if aerosol_files:
        aerosol_data, aerosol_var_names = get_aerosol_data_from_file(
            aerosol_files[0], image_shape)

        for w, name in enumerate(aerosol_var_names):
            data_layer_dict[str(name)] = (
                LayerType.AEROSOL,
                aerosol_data[..., w],
            )

    # Add Sun-View Geometry to the dict
    if add_geom:
        for a, attr in enumerate(view_geometry_names):
            data_layer_dict[attr] = (
                LayerType.VIEW_GEO,
                view_geometry[..., a],
            )

    # Add the nan mask to the dict
    if add_nan_mask:
        data_layer_dict["NaN Mask"] = (LayerType.NAN_MASK, nan_masks)

    if add_sid:
        data_layer_dict["Surface IDS"] = (LayerType.SURFACE_ID, sid)

    # Add the MAIA cloud mask to the dict
    if add_cloud_mask:
        data_layer_dict["Cloud Mask"] = (LayerType.CLOUD_MASK, cloud_masks)

    ancillary_config = {
        'number_of_activations_needed': activations_needed,
        'activation_values': activation_values_arr,
        'fill_val_2': fill_val_2_list,
        'fill_val_3': fill_val_3_list,
    }

    output_template = mask_files[0].replace(views[0],
                                            '<view>') if mask_files else ''

    return data_layer_dict, output_template, image_shape, ancillary_config, (
        views, angles)
