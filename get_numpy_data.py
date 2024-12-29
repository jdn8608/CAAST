"""
This module determines which instrument file reader to call to ingest data for visualization and calls it accordingly 
"""
import file_readers
import numpy as np
import json


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


def get_data(parent_dir, instrument_name, reader_config_filepath=None):
    """Calls the corresponding module to ingest instrument imager data

     Args:
        parent_dir: the directory for where the input file is located
        instrument_name: the name of the instrument to select the corresponding file reader
        reader_config_filepath: filepath to the JSON file for extra configurations that may be needed by the file reader

     Returns:
        the output from the file reader call (see README for guidelines)
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
        return file_reader(parent_dir,
                           search=config["filename_search_string"],
                           view=config["view"],
                           bands_to_get=config["bands"],
                           add_cloud_mask=config["load_labels"].upper()=="CLOUD MASK",
                           add_nan_mask=config["create_nan_mask"]
                           ), config["view"], config["angle"]
    else:
        # Raise an exception if no file reader is found for the given name
        raise Exception(f'''file reader not found for instrument name: 
        "{instrument_name}"\n
        Please see the README for how to add file readers.''')
