
from tqdm.notebook import tqdm

import random
import pickle
import glob
import os
import argparse
import json

from get_numpy_data import get_data
from visualize import single_view_multi_band

'''
TO DO:
	-ITERATE ON PASS IN FUNCTIONALITY
	-ADD OS SEPERATOR FUNCTIONALITY FOR WINDOWS
	-ADD MULTI-ANGLE CAPABILITY
	-DOCUMENT DOCUMENT DOCUMENT
		-REQUIRMENTS.TXT
'''

def get_output_settings(json_file, input_filename):	
	with open(json_file, 'r') as file:
		output_file_configs = json.load(file)
	if output_file_configs["override_filename"]:
		return output_file_configs["override_filename"], output_file_configs["dataset_name"]
	elif output_file_configs["override_filepath"]:
		return output_file_configs["override_filepath"]+input_filename.split('.')[0].split(os.sep)[-1]+output_file_configs["append_name"]+output_file_configs["file_type"], output_file_configs["dataset_name"]
	else:
		return input_filename.split('.')[0]+output_file_configs["append_name"]+output_file_configs["file_type"], output_file_configs["dataset_name"]
		

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		prog="RS-PL",
		description="Remote Sensing - Pixel Label (RS-PL) tool:\n This tool was developed to have an easy, quick, and accesible tool to label imagery from various remote sensing platforms.",
		epilog='Tool is currently under developement. For more information, goto GITHUB_LINK')

	# required arguments
	parser.add_argument('dir', 
		help="root directory to retrieve files from")
	parser.add_argument('instrument_name', 
		help="instrument that we will be reading in data for. This will determine how to read in data, (i.e., determine the file reader). See the README for more details.")

	# optional arguments
	parser.add_argument('-o','--output_settings_file',
		help="file containing the output settings to save the labels created by the user. See the README for more details.",
		default='./util_files/output_settings_default.json')
	parser.add_argument('-ma', '--multiangle', 
		help="turn on multi-angle use", 
		action='store_true')
	parser.add_argument('-rc', '--reader_config', 
		help="Path to a .json file for additional information to use by the instrument file reader, if it is needed.")
	parser.add_argument('-vc', '--vis_config', 
		help="Path to a .json file for additional information and options to use by the visualization script/software.",
		default='./util_files/default_vizconfig.json')
	parser.add_argument('-v', '--verbose',
		action='store_true')

	# compile args
	args = parser.parse_args()
	# retrieve data
	data, band_names, load_labels, input_filename = get_data(args.dir, args.instrument_name,
		multiangle=args.multiangle,
		reader_config_file=args.reader_config
		)
	if not args.multiangle:
		output_filename, dataset_name = get_output_settings(args.output_settings_file, input_filename)
		single_view_multi_band(data=data, 
			band_names=band_names, 
			output_filepath=output_filename,
			prior_labels=load_labels, 
			dataset_name=dataset_name,
			vis_config_file=args.vis_config)
	else:
		print('TBD')

	quit()
