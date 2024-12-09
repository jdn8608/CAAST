import argparse
import glob
import json
import os
from pathlib import Path

from get_numpy_data import get_data
from visualize import create_napari_visualization
'''
TO DO:
	-ITERATE ON PASS IN FUNCTIONALITY
	-ADD OS SEPERATOR FUNCTIONALITY FOR WINDOWS
	-DOCUMENT DOCUMENT DOCUMENT
		-REQUIRMENTS.TXT
'''


def get_output_settings(json_file, input_filepath):
    with open(json_file, 'r') as file:
        config = json.load(file)
    if config["override_filename"]:
        filename = config["output_file_configs"]
    else:
        filename = os.path.splitext(os.path.basename(input_filepath))[0]

    if config["override_dirpath"]:
        dirpath = config["override_dirpath"]
    else:
        dirpath = os.path.dirname(input_filepath)

    return os.path.join(dirpath, filename + config["append_name"] +
                        config["file_type"]), config["dataset_name"]


if __name__ == "__main__":

    # set-up arge parser
    parser = argparse.ArgumentParser(
        prog="RS-PL",
        description=
        "Remote Sensing - Pixel Label (RS-PL) tool:\n This tool was developed to have an easy, quick, and accesible tool to label imagery from various remote sensing platforms.",
        epilog=
        'Tool is currently under developement. For more information, goto GITHUB_LINK'
    )

    # required arguments
    parser.add_argument('dir', help="root directory to retrieve files from")
    parser.add_argument(
        'instrument_name',
        help=
        "instrument that we will be reading in data for. This will determine how to read in data, (i.e., determine the file reader). See the README for more details."
    )

    # optional arguments
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
        "Path to a .json file for additional information to use by the instrument file reader, if it is needed."
    )
    parser.add_argument(
        '-v',
        '--vis_config',
        help=
        "Path to a .json file for additional information and options to use by the visualization script/software.",
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

    # compile args
    args = parser.parse_args()

    # retrieve data
    (data, band_names, prior_mask, input_filename), views, angles = get_data(
        args.dir, args.instrument_name, reader_config_file=args.reader_config)

    output_filename, dataset_name = get_output_settings(
        args.output_settings_file, input_filename)

    # settings flag: if output file exists, and if labels are desired, this flag will let them to be loaded in
    prior_manual_labels = args.check_manual_labels

    create_napari_visualization(data=data,
                                band_names=band_names,
                                output_filepath=output_filename,
                                prior_mask=prior_mask,
                                prior_manual_labels=prior_manual_labels,
                                load_labels=args.load_labels,
                                dataset_name=dataset_name,
                                vis_config_file=args.vis_config,
                                views=views,
                                angles=angles)
