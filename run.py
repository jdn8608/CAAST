"""
Author: Joseph Nied (jdnied2@illinois.edu)
Date: 12-19-2024
Description:
    The main run script for the PL-RS visualization tool to be ran from the command line.

    This script sub-modules with settings from configuration files to read-in, format, & 
    visualize satelitte imager data. 
"""

import argparse
import json
import os

from get_data import get_data
# from visualize import visualize

if __name__ == "__main__":

    # Set-up arge parser
    #Decsriptions for all pass-in parameters are provided in their declaration under <help>
    parser = argparse.ArgumentParser(
        prog="RS-PL",
        description=
        "Remote Sensing - Pixel Label (RS-PL) tool:\n This tool was developed to have an easy, quick, and accesible tool to label imagery from various remote sensing platforms.",
        epilog=
        'Tool is currently under developement. For more information, goto https://github.com/jdn8608/PL-RS'
    )

    # Required arguments
    parser.add_argument('dir', help="root directory to retrieve files from")
    parser.add_argument(
        'instrument_name',
        help=
        "instrument that we will be reading in data for. This will determine how to read in data, (i.e., determine the file reader). See the README for more details."
    )

    # Optional arguments
    parser.add_argument(
        '-m',
        '--label_mode',
        help=
        "flag to set the tool in label mode. If not set, tool will be in review only mode. See README for more details",
        action='store_true')
    parser.add_argument(
        '-o',
        '--output_settings_file',
        help=
        "file containing the output settings to save the labels created by the user. See the README for more details.",
        default='./util_files/output_settings_default.json')
    parser.add_argument(
        '-r',
        '--reader_config',
        help=
        "Path to a JSON file for additional information to use by the instrument file reader, if it is needed."
    )
    parser.add_argument(
        '-v',
        '--vis_config',
        help=
        "Path to a JSON file for additional information and options to use by the visualization script/software.",
        default='./util_files/default_vizconfig.json')
    parser.add_argument(
        '-c',
        '--check_manual_labels',
        help=
        "Flag to check for if manual labels already exists, based on the OUTPUT_SETTINGS_FILE settings. If a file is found, these labels will be loaded as an additional layer. If no file is found, this flag does nothing.",
        action='store_true')
    parser.add_argument(
        '-l',
        '--load_labels',
        help=
        "Pass in argument to select what labels to load into the Editing layer. Values can be 'mask' or 'manual'. If not provided, Editing layer will be loaded with 1s or 0s. IF mask is selected: the file reader needs to return the mask and load_labels=True. IF manual selected, the -l parameter needs to be passed and the file needs to be detected. If either case fails, default settings of None are selected.",
        default=None)
    parser.add_argument('-V', '--verbose', action='store_true')

    # Compile args passed in from the command line by the user
    args = parser.parse_args()

    # Call get_data() to get the data to visualize. This calls the correct instrument filereader module to ingest the data
    # The filereader will create a formatted dict for the ingested data -> data_layer_dict
    output_filepath, views, angles, data_layer_dict, shape, scene_attrs, review_data = get_data(
        parent_dir=args.dir,
        instrument_name=args.instrument_name,
        output_settings_filepath=args.output_settings_file,
        reader_config_filepath=args.reader_config,
        label_mode=args.label_mode,
        load_prior_manual_labels=args.check_manual_labels)

    # Forward read-in data and pass-in variable to the visualization script that will generate the GUI + necessary widgets
    #visualize(data=data_layer_dict,
    #          output_filepath=output_filename,
    #          label_mode=args.label_mode,
    #          review_mode_csv_filepath=review_mode_csv_filepath,
    #          prior_manual_labels=args.check_manual_labels,
    #          load_labels=args.load_labels,
    #          dataset_name=dataset_name,
    #          vis_config_file=args.vis_config,
    #          views=views,
    #          angles=angles)
