import file_readers 
import json

def create_instrument_dict_single_view():
	reader_dict = {
		'MAIA' 	: file_readers.MAIA_singleview.read,
		'MODIS'	: file_readers.MODIS.read,
		'MISR' 	: file_readers.MISR_singleview.read,
		}
	return reader_dict

def create_instrument_dict_mutli_view():
	reader_dict = {
		'MAIA' 	: file_readers.MAIA_multiview.read,
		'MISR' 	: file_readers.MISR_multiview.read,
		}
	return reader_dict

def error_not_found(instrument_name):
	error_out = f'file reader not found for instrument name: "{instrument_name}"\nPlease see the README for how to add file readers.'
	raise Exception(error_out)

def get_data(parent_dir, instrument_name, multiangle=False, reader_config_file=None):
	metadata = None
	if reader_config_file:
		with open(reader_config_file, 'r') as file:
			config = json.load(file)	

	# load the filereader dictionary needed 
	if not multiangle:
		reader_dict = create_instrument_dict_single_view()
	else:
		reader_dict = create_instrument_dict_multi_view()

	file_reader = reader_dict.get(instrument_name, None)
	if file_reader:
		return file_reader(parent_dir, config=config)	
	else:
		error_not_found(instrument_name)

