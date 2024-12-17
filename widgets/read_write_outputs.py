import numpy as np
import h5py as h5
import xarray as xr
import datetime
from tqdm import tqdm
import os
from colorama import Fore, Style
import errno
import pandas as pd
import json


def save_labels(output_filepath,
                labels=None,
                dataset_name=None,
                views=None,
                scene_labels_dict=None,
                review_filepath='./labels/cloud_mask_review.csv',
                review_dropdown=None,
                review_grader=None):

    if not review_dropdown is None and not review_grader is None:

        try:
            df = pd.read_csv(review_filepath)
        except FileNotFoundError:
            # If the file doesn't exist, initialize a new DataFrame with appropriate columns
            df = pd.DataFrame(columns=[
                'filename', 'cloud_mask_status', 'cloud_mask_grade',
                'entry_date_time'
            ])
        new_row = {
            "filename":
            output_filepath,
            "cloud_mask_status":
            review_dropdown.currentText(),
            "cloud_mask_grade":
            review_grader.value,
            "entry_date_time":
            datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S")  # Format datetime as string
        }
        df = df[df['filename'] != new_row['filename']]
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(review_filepath, index=False)
        print(
            f"{datetime.datetime.now()}: review evaluation saved to {review_filepath}"
        )

    if scene_labels_dict:

        scene_attributes = {
            label: combo_box.currentText()
            for label, combo_box in scene_labels_dict.items()
        }
        scene_labels_output_filepath = format_scene_label_file(output_filepath)
        scene_labels_write(scene_labels_output_filepath, scene_attributes)
        print(
            f"{datetime.datetime.now()}: scene labels saved to {scene_labels_output_filepath}"
        )

    if not labels is None:
        filetype = output_filepath.split('.')[-1]
        if filetype == 'npy':
            writer = npy_write
        elif filetype == 'hdf' or filetype == 'hdf5':
            writer = hdf_write
        elif filetype == 'nc':
            writer = nc_write
        else:
            raise Exception(
                f"filetype '{filetype}' id not currently supported for saving files.\n please use a different filetype for output, or add functionality for this filetype"
            )

        for v, view in enumerate(tqdm(views, desc="Saving File(s)")):
            pixel_labels_output_filepath = format_output_filepath_views(
                output_filepath, view)
            writer(pixel_labels_output_filepath, dataset_name, labels[:, :, v])
            tqdm.write(
                f"{datetime.datetime.now()}: pixel labels saved to {pixel_labels_output_filepath}"
            )


def format_output_filepath_views(filepath, view):
    return filepath.replace('<view>', view)


def npy_read(filepath, dataset_name):
    d = np.load(filepath, allow_pickle=True)
    return np.load(filepath, allow_pickle=True)


def npy_write(filepath, dataset_name, data):
    np.save(filepath, data)


def nc_read(filepath, dataset_name):
    ds = xr.open_dataset(filepath)
    data = ds[dataset_name].values  # Assuming "labels" is the dataset name
    ds.close()
    return data


def nc_write(filepath, dataset_name, data):
    da = xr.DataArray(data, dims=("y", "x"), name=dataset_name)
    ds = xr.Dataset({dataset_name: da})
    ds.to_netcdf(filepath)


def hdf_read(filepath, dataset_name):
    h5_dataset = h5.File(filepath, "r")
    data = h5_dataset[dataset_name][:]
    h5_dataset.close()
    return data


def hdf_write(filepath, dataset_name, data):
    out_file = h5.File(filepath, "w")
    h5_dataset = out_file.create_dataset(dataset_name, data=data)
    out_file.close()


def format_scene_label_file(filepath):
    return f'{os.path.splitext(filepath)[0]}_scenelabels.json'.replace(
        "<view>", "ALL")


#def scene_labels_read(filepath):
#    scene_attributes = {}
#    with open(filepath, 'r') as txt_file:
#        for line in txt_file:
#            key, value = tuple(line.split(" : "))
#            value = value.strip()
#            scene_attributes[key] = value
#    return scene_attributes
#
#
#def scene_labels_write(filepath, scene_attributes):
#
#    with open(filepath, "w") as txt_file:
#        for key, value in zip(scene_attributes.keys(),
#                              scene_attributes.values()):
#            txt_file.write(f"{key} : {value}\n")
#
#    return
#
def scene_labels_read(filepath):
    """
    Reads a JSON file and returns the contents as a dictionary.
    """
    with open(filepath, 'r') as json_file:
        scene_attributes = json.load(json_file)
    return scene_attributes


def scene_labels_write(filepath, scene_attributes):
    """
    Writes a dictionary to a JSON file.
    """
    with open(filepath, "w") as json_file:
        json.dump(scene_attributes, json_file, indent=4)


def check_file_exists(filepath):
    if os.path.exists(filepath):
        return
    else:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT),
                                filepath)


def read_labels(output_filepath,
                dataset_name,
                views,
                review_filepath='./labels/cloud_mask_review.csv',
                scene_attrs=False):
    if scene_attrs:
        scene_label_filepath = format_scene_label_file(output_filepath)
        check_file_exists(scene_label_filepath)
        scene_attributes = scene_labels_read(scene_label_filepath)

    if review_filepath:
        df = pd.read_csv(review_filepath)
        df = df[df['filename'] == output_filepath]
        review_grade = df['cloud_mask_grade'][0]
        review_status = df['cloud_mask_status'][0]
    else:
        review_grade = None
        review_status = None

    filetype = output_filepath.split('.')[-1]
    if filetype == 'npy':
        reader = npy_read
    elif filetype == 'hdf' or filetype == 'hdf5':
        reader = hdf_read
    elif filetype == 'nc':
        reader = nc_read
    else:
        raise Exception(
            f"filetype '{filetype}' id not currently supported for reading files.\n please use a different filetype for output, or add functionality for this filetype"
        )
    try:
        check_file_exists(
            format_output_filepath_views(output_filepath, views[0]))
        X, Y = reader(format_output_filepath_views(output_filepath, views[0]),
                      dataset_name).shape
        labels = np.zeros((X, Y, len(views)))
        for v, view in enumerate(tqdm(views, "Loading Prior Label File(s)")):
            label_view_filepath = format_output_filepath_views(
                output_filepath, view)
            check_file_exists(label_view_filepath)
            labels[:, :, v] = reader(label_view_filepath, dataset_name)
    except FileNotFoundError as error:
        print(Fore.RED + f"Error encountered: {error}")
        print(Fore.YELLOW +
              "Prior labels file was not found (see error above)")
        print("Fore-going loading prior labels")
        print(Style.RESET_ALL)
        labels = None

    return labels, scene_attributes, review_grade, review_status
