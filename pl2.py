
from tqdm.notebook import tqdm

import random
import pickle
import glob
import os
import argparse

from get_numpy_data import get_data
from visualize import single_view_multi_band

'''
TO DO:
	-ITERATE ON PASS IN FUNCTIONALITY
	-ADD MULTI-ANGLE CAPABILITY
	-DOCUMENT DOCUMENT DOCUMENT
		-REQUIRMENTS.TXT
'''

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		prog="RS-PL",
		description="Remote Sensing - Pixel Label (RS-PL) tool:\n This tool was developed to have an easy, quick, and accesible tool to label imagery from various remote sensing platforms.",
		epilog='Tool is currently under developement. For more information, goto GITHUB_LINK')

	# required arguments
	parser.add_argument('dir', 
		help="root directory to retrieve files from")
	parser.add_argument('instrument_name', 
		help="instrument that we will be reading in data for. This will determine how to read in data, (i.e., determine the file reader). See the README.")
	#parser.add_argument('files', 
	#	help="files to read in. If --multiangle is off, only first file will be read",
	#	nargs='+')

	# optional arguments
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
	data, band_names, load_labels = get_data(args.dir, args.instrument_name,
		multiangle=args.multiangle,
		reader_config_file=args.reader_config
		)
	print(args.vis_config)	
	if not args.multiangle:
		single_view_multi_band(data, band_names=band_names, prior_labels=load_labels, vis_config_file=args.vis_config)
	else:
		print('TBD')

	quit()
