
from tqdm.notebook import tqdm

import random
import pickle
import glob
import os
import argparse



'''
TO DO:
	-INGEST ARGS
	-CREATE GET_DATA SCRIPT
	-CREATE SATELITTE FILE READER FOR GET_DATA
		-JUST MAIA NADIR FOR NOW
	-VISUALIZATION SCRIPT
	-ITERATE ON PASS IN FUNCTIONALITY
	-ADD MULTI-ANGLE CAPABILITY
	-DOCUMENT DOCUMENT DOCUMENT
		-REQUIRMENTS.TXT
'''

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		prog="RS-PL",
		description="Remote Sensing - Pixel Label (RS-PL) tool:\n This tool was developed to have an easy, quick, and accesible tool to label imagery from various remote sensing platforms.",
		epilog='Tool is currently under developement. For more information, got to GITHUB_LINK')

	parser.add_argument('dir', 
		help="root directory to retrieve files from")
	parser.add_argument('files', 
		help="files to read in. If --multiangle is off, only first file will be read",
		nargs='+')
	parser.add_argument('-ma', '--multiangle', 
		help="turn on multi-angle use", 
		action='store_true')
	parser.add_argument('-v', '--verbose',
		action='store_true')
	args = parser.parse_args()
	print(args.dir)
	print(args.files)
	quit()
