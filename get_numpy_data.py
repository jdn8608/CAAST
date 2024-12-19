import file_readers
import numpy as np
import json


def create_instrument_dict():
    reader_dict = {
        'MAIA': file_readers.MAIA.read,
        'MISR': file_readers.MISR.get_multiangle,
    }
    return reader_dict


def get_data(parent_dir, instrument_name, reader_config_filepath=None):


def get_data(parent_dir, instrument_name, reader_config_file=None):
    metadata = None
    if reader_config_file:
        with open(reader_config_file, 'r') as file:
            config = json.load(file)

    reader_dict = create_instrument_dict()

    file_reader = reader_dict.get(instrument_name, None)
    if file_reader:
        return file_reader(parent_dir,
                           search=config["filename_search_string"],
                           view=config["view"],
                           bands_to_get=config["bands"],
                           get_cloud_mask=config["load_labels"]
                           ), config["view"], config["angle"]
    else:
        raise Exception(f'''file reader not found for instrument name: 
        "{instrument_name}"\n
        Please see the README for how to add file readers.''')
