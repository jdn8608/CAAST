"""
Author: Joseph Nied (jdnied2@illinois.edu)
Date: 12-19-2024
Description:
    The main run script for the SALT visualization tool to be ran from the command line.

    This script sub-modules with settings from configuration files to read-in, format, & 
    visualize satelitte imager data. 
"""

import argparse
import json
import os

# Import util scripts
from util.get_data import get_data
from util.create_tool import create_tool

# Meta-data for file
__author__ = "Joseph Nied"
__credits__ = ["Joseph Nied"]
__copyright__ = "Copyright 2007"
__license__ = "GPL"
__version__ = "3.0"
__maintainer__ = "Joseph Nied"
__email__ = "jdnied2@illinois.edu"
__status__ = "Production"


def get_from_GUI():
    return


def get_from_command_line():
    return


def get_from_settings_files():
    return


if __name__ == "__main__":

    # Set-up arge parser
    #Decsriptions for all pass-in parameters are provided in their declaration under <help>
    parser = argparse.ArgumentParser(
        prog="RS-PL",
        description=
        "Remote Sensing - Pixel Label (RS-PL) tool:\n This tool was developed to have an easy, quick, and accesible tool to label imagery from various remote sensing platforms.",
        epilog=
        'Tool is currently under developement. For more information, goto https://github.com/jdn8608/SALT'
    )

    # Required arguments
    parser.add_argument(
        'parameter_mode',
        help=
        """Tells the software in what mode to receive option selections from the user.
                        Valid string options are 'GUI'(G), 'SETTINGS'(S), or 'COMMAND'(C), where the letters in parenthesis can be used for shortened indicators.
                        GUI mode opens a GUI interface for the users to select options.\n
                        SETTINGS mode opens the settings files provided under the attriburtes --reader_config --vis_config
                        --output_config list below\n
                        COMMAND mode uses all command line attributes below, and takes preference of information from command line over settings files""",
    )

    # Optional arguments
    parser.add_argument(
        '-d',
        '--dir',
        help="root directory to retrieve files from",
    )
    parser.add_argument(
        '-i',
        '--instrument_name',
        help=
        "instrument that we will be reading in data for. This will determine how to read in data, (i.e., determine the file reader). See the README for more details."
    )
    parser.add_argument(
        '-s',
        '--scene_identifier',
        help=
        "A string to indicate file(s) to retrieve within the provided 'dir'. Furthermore, wildcards are acceptable as the character '*'. Note: for multiangle viewers, such as MAIA, <views> vars may be retrieved from the settings files and are thus not needed in this search string."
    )
    parser.add_argument(
        '-m',
        '--label_mode',
        help=
        "flag to set the tool in label mode. If not set, tool will be in review only mode. See README for more details",
        action='store_true')
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
        default='./settings/default_vizconfig.json')

    parser.add_argument(
        '-o',
        '--output_config',
        help=
        "file containing the output settings to save the labels created by the user. See the README for more details.",
        default='./settings/output_settings_default.json')
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
    settings_mode = args.parameter_mode.upper()
    if settings_mode == 'G' or 'GUI' in settings_mode:
        pass
    elif settings_mode == 'S' or 'SETTINGS' in settings_mode:
        pass
    elif settings_mode == 'C' or 'COMMAND' in settings_mode:
        pass
    else:
        raise Exception("Invalid 'settings_mode' attribute value"
                        "Please refer to --help for valid options")


    # Call get_data() to get the data to visualize. This calls the correct instrument filereader module to ingest the data
    # The filereader will create a formatted dict for the ingested data -> data_layer_dict
    output_file_info, views, angles, data_layer_dict, shape, ancillary_config, \
        scene_attrs, review_csv_filepath, review_data, notes = get_data(
            parent_dir=args.dir,
            instrument_name=args.instrument_name,
            search_string=args.scene_identifier,
            output_settings_filepath=args.output_settings_file,
            reader_config_filepath=args.reader_config,
            label_mode=args.label_mode,
            load_prior_manual_labels=args.check_manual_labels)

    # Call create_tool to create and open the application
    create_tool(args.label_mode,
                data_layer_dict,
                shape,
                output_file_info,
                views,
                angles,
                ancillary_config,
                scene_attrs,
                review_csv_filepath,
                review_data,
                notes,
                load_labels_name=args.load_labels if args.label_mode else '',
                config_filepath=args.vis_config)
