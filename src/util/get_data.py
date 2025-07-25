"""
This module determines which instrument file reader to call to ingest data for visualization and calls it accordingly 
"""
import json
import os

import numpy as np

import file_readers
from util.LayerType import LayerType
from util.read_write_outputs import read_labels


def create_instrument_dict():
    """Function to define a dictionary of instrument file reader modules

    Returns:
        a dicrtionary, where the keys are strings of instrument names and the values are the modules 
        used to ingest that instrument's data
    """
    reader_dict = {
        'MAIA': file_readers.MAIA.read,
        'MISR': file_readers.MISR.get_multiangle,
        'ML64': file_readers.ML_64x64.read
    }
    return reader_dict


def get_instrument_layer_data(parent_dir,
                              instrument_name,
                              search_string,
                              config=None):
    """Calls the corresponding module to ingest instrument imager data

     Args:
        parent_dir: the directory for where the input file is located
        instrument_name: the name of the instrument to select the corresponding file reader
        config: the config dict for ingesting instrument data. Provides settings like what views
            to load, what kind of data to load, etc. Config dict is passed if there are additional
            details need for an instrument besides the standardized pass-in vars.

     Returns:
        the output from the file reader call: a dictionary of instrument data and a filepath to input files
        (see README for guidelines)

    Exception:
        an exception is thrown if a file_reader is not found for the instrument name provided
    """
    # get the instrument dict (dict of sub-module function calls)
    reader_dict = create_instrument_dict()

    # Override instrument name from config if provided
    if config and "file_reader" in config:
        instrument_name = config["file_reader"]

    file_reader = reader_dict.get(instrument_name, None)
    if file_reader:
        # TODO: Might remove search string altogether
        if config and "files" in config:
            return file_reader(parent_dir,
                               files=config["files"],
                               config=config)
        else:
            return file_reader(parent_dir,
                               search=search_string,
                               views=config["view"],
                               config=config)

    else:
        # Raise an exception if no file reader is found for the given name
        raise Exception(f'''file reader not found for instrument name:
        "{instrument_name}"\n
        Please see the README for how to add file readers.''')


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


def get_review_mode_output_settings(json_filepath):
    """ Get the configurations for the review mode of the tool

      Args:
          json_filepath: the filepath to the review mode configuration JSON file

      Returns:
          a dictionairy of the review_mode configuration settings
      """
    with open(json_filepath, 'r') as file:
        config = json.load(file)
    return config['review-mode_csv_filepath']


def get_data(
    parent_dir,
    instrument_name,
    search_string,
    output_settings_filepath,
    reader_config_filepath,
    label_mode=False,
    load_prior_manual_labels=False,
):
    """Calls get sub-functions to ingest various data(sets) for the toolkit

    Args:
        parent_dir: the directory for where the input file is located
        instrument_name: the name of the instrument to select the corresponding file reader
        config: the config dict for ingesting instrument data. Provides settings like what views
            to load, what kind of data to load, etc. Config dict is passed if there are additional
            details need for an instrument besides the standardized pass-in vars.

    Returns:
        (output_filepath_convention, dataset_name) : the output_filepath and the name of the dataset
            to keep where the user wants to save files out to
        views : the names of the views for this insturment
        angles : the view angle for each view of this instrument
        data_layer_dict :  a dictionairy, where the keys are the name of the layer data for the
            tool/visualization, and the values are tuples of (layer type, NumPy data array).
        scene_attrs : a list or dict. If list, the attributes wanted to create scene-level labels
            by the user. If a dict, the dictionary of these attributes and past labels provided
            by the user.
        review_csv_filepath : the filepath to the csv file for review mode grading. None if not in
            review mode.
        (review_grade, review_status) : the past review grade and approve/reject status of this scene
            if previously graded. If not or not in review mode, the default value is None.
        notes : a string of the user's last notes if created. If not, default value is None
    """
    # Open the file reader configuration JSON file into a dict
    if reader_config_filepath:
        with open(reader_config_filepath, 'r') as file:
            config = json.load(file)

    # Get instrument NumPy Layer data (and input file location)
    reader_out = get_instrument_layer_data(
        parent_dir, instrument_name, search_string, config)

    # Parse outputs from the file reader
    if len(reader_out) == 6:
        data_layer_dict, input_filepath, shape, ancillary_config, views, angles = reader_out
    elif len(reader_out) == 5:
        data_layer_dict, input_filepath, shape, ancillary_config, (views, angles) = reader_out
    elif len(reader_out) == 4:
        data_layer_dict, input_filepath, shape, (views, angles) = reader_out
        ancillary_config = None
    else:
        data_layer_dict, input_filepath, shape = reader_out
        ancillary_config = None
        views = config.get("view") if config else None
        angles = config.get("angle") if config else None

    # Get the filepath and dataset name to save out pixel labels
    output_filepath_convention, dataset_name = get_general_output_settings(
        output_settings_filepath, input_filepath)

    # If we are not in pixel labeling mode, we need to provide the settings for review mode
    if not label_mode:
        review_csv_filepath = get_review_mode_output_settings(
            output_settings_filepath)
    else:
        review_csv_filepath = None

    # If flag is on, attempt to find and read prior manual label file(s)
    if load_prior_manual_labels:
        manual_labels, scene_attrs, review_grade, review_status, notes = read_labels(
            output_filepath=output_filepath_convention,
            dataset_name=dataset_name,
            views=views,
            review_filepath=review_csv_filepath,
            scene_attrs=config["scene_labels"])

        # add the prior manual labels to the data layer dict
        data_layer_dict["Manual Labels"] = (LayerType.MANUAL_LABELS,
                                            manual_labels)

    else:
        # If flag is off, set default values
        scene_attrs = config["scene_labels"]
        review_grade = None
        review_status = None
        notes = None

    return (output_filepath_convention, dataset_name), views, angles, data_layer_dict, \
        shape, ancillary_config, scene_attrs, review_csv_filepath, (review_grade, review_status), notes
