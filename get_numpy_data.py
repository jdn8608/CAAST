"""
This module determines which instrument file reader to call to ingest data for visualization and calls it accordingly 
"""
import json

import numpy as np

import file_readers
from util_files.read_write_outputs import read_labels


def create_instrument_dict():
    """Function to define a dictionary of instrument file reader modules

    Returns:
        a dicrtionary, where the keys are strings of instrument names and the values are the modules used to ingest that instrument's data
    """
    reader_dict = {
        'MAIA': file_readers.MAIA.read,
        'MISR': file_readers.MISR.get_multiangle,
    }
    return reader_dict


def get_general_output_settings(json_filepath, input_filepath):
    """
    Args:
        json_filepath:  the file path to ingest/format output file settings
        input_filepath: the filepath to the input file that is ingested for visualization

    Returns:
        an os formated string to the pixel-label output file, and the name for the dataset in the file
    """
    # Open the JSON file as a dictionary
    with open(json_filepath, 'r') as file:
        config = json.load(file)

    # Get the filename pattern to override the input filename, if set
    if config["override_filename"]:
        filename = config["output_file_configs"]
    else:
        filename = os.path.splitext(os.path.basename(input_filepath))[0]

    # Get the dir path for the output file if provided, otherwise use that from the input file
    if config["override_dirpath"]:
        dirpath = config["override_dirpath"]
    else:
        dirpath = os.path.dirname(input_filepath)

    return os.path.join(dirpath, filename + config["append_name"] +
                        config["file_type"]), config["dataset_name"]


def get_data(parent_dir,
             instrument_name,
             output_settings_filepath,
             load_prior_manual_labels=False,
             reader_config_filepath=None):
    """Calls the corresponding module to ingest instrument imager data

     Args:
        parent_dir: the directory for where the input file is located
        instrument_name: the name of the instrument to select the corresponding file reader
        reader_config_filepath: filepath to the JSON file for extra configurations that may be needed by the file reader

     Returns:
        the output from the file reader call: a dictionary of instrument data and a filepath to input files
        (see README for guidelines)
    """
    # Open the file reader configuration JSON file into a dict
    if reader_config_filepath:
        with open(reader_config_filepath, 'r') as file:
            config = json.load(file)

    # get the instrument dict (dict of sub-module function calls)
    reader_dict = create_instrument_dict()

    # Select and call the file reader based on the str name
    file_reader = reader_dict.get(instrument_name, None)
    if file_reader:
        data_layer_dict, input_filepath = file_reader(
            parent_dir,
            search=config["filename_search_string"],
            views=config["view"],
            bands_to_get=config["bands"],
            add_cloud_mask=config["load_labels"].upper() == "CLOUD MASK",
            add_nan_mask=config["create_nan_mask"])

        output_filepath_convention, dataset_name = get_general_output_settings(
            output_settings_filpeath, input_filepath)

        if load_prior_manual_labels:
            # read_labels(output_filename_convention, views=config["view"])
            pass
        return data_layer_dict, output_filename_convention, config[
            "view"], config["angle"]
    else:
        # Raise an exception if no file reader is found for the given name
        raise Exception(f'''file reader not found for instrument name: 
        "{instrument_name}"\n
        Please see the README for how to add file readers.''')
