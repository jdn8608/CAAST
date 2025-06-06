"""
Module for reading and writing output files for the toolkit.

Output includes that for pixel labeling, scene labels, notes, or review mode grading.

Module allows for mutliple pixel labling lfileitypes to be used. Currently, .npy, .h5, and .nc 
are supported. If there are other types desired, open up an issue thread on the GitHub page.
"""
import datetime
import errno
import json
import os

from colorama import Fore, Style
from tqdm import tqdm

import h5py as h5
import numpy as np
import pandas as pd
import xarray as xr


def save_labels(output_filepath,
                labels=None,
                dataset_name=None,
                views=None,
                scene_labels_dict=None,
                review_filepath='./labels/cloud_mask_review.csv',
                review_dropdown=None,
                review_grader=None,
                notes_textbox=None):
    """"saves various output files depending on optional pass-in vars
    Args:
        output_filepath: pixel label output filepath string, with the '<view>' sub-string (if a multi-angle imager)
        labels: a numpy array of the prior manual pixel labels read in with a shape (HEIGHT, WIDTH, NUMBER OF VIEWS)
        views: list of strings representing diferent views for a multi-angle imager
        scene_labels_dict: a dict of the scene label variables and the corresponding values 
        review_filepath: filepath to the CSV file for review/evaluation of various scenes

        dataset_name: the name of the dataset saved in the file
        scene_attrs: boolean stating whether to attempt to read-in the scene labels file

        review_grade: int number representing the quality of the operational labels (typically values 1-5)
        review_status: string representing whether this scene is 'Ungraded'  'Accepted' or 'Rejected' 
        notes: a string of the user's prior notes
    """
    # Update grade labels
    if not review_dropdown is None and not review_grader is None:

        try:
            df = pd.read_csv(review_filepath)
        except FileNotFoundError:
            # If the file doesn't exist, initialize a new DataFrame with appropriate columns
            df = pd.DataFrame(columns=[
                'filename', 'cloud_mask_status', 'cloud_mask_grade',
                'entry_date_time'
            ])
        # Create a new entry row
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
        # Check if entry exists aleady, if so, remove it
        df = df[df['filename'] != new_row['filename']]
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(review_filepath, index=False)
        print(
            f"{datetime.datetime.now()}: review evaluation saved to {review_filepath}"
        )

    # Save of scene labels
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

    # Save the text wihtin the textbox
    if notes_textbox:
        scene_labels_output_filepath = format_scene_label_file(output_filepath)
        scene_labels_write(scene_labels_output_filepath,
                           {'notes': notes_textbox.toPlainText()})
        print(
            f"{datetime.datetime.now()}: notes text saved to {scene_labels_output_filepath}"
        )

    # Save the pixel labels based on file type, for all view angles
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
            writer(pixel_labels_output_filepath, dataset_name, labels[v])
            tqdm.write(
                f"{datetime.datetime.now()}: pixel labels saved to {pixel_labels_output_filepath}"
            )


def format_output_filepath_views(filepath, view):
    """formats a filepath string with the current view

    Args:
        filepath: a filepath containing the sub-string '<view>'
        view: a string representing a viewing direction, such as the nameing convention for MISR of AN, BC, etc.

    Returns:
        the string in filepath with '<view>' replaced with the string in the view variable
    """
    return filepath.replace('<view>', view)


def npy_read(filepath, dataset_name):
    """function to read in pixel labels in the NPY (.npy) format

    Args:
        filepath: string for the filepath to the output file for the pixel labels
        dataset_name: the name of the dataset saved in the file

    Rerturns:
        a numpy array of the output pixel labels
    """
    d = np.load(filepath, allow_pickle=True)
    return np.load(filepath, allow_pickle=True)


def npy_write(filepath, dataset_name, data):
    """function to write pixel labels to a NPY (.npy) formatted file

    Args:
        filepath: string for the filepath to the output file for the pixel labels
        dataset_name: the name of the dataset saved in the file
        data: a numpy array of shape (HEIGHT, WIDTH)
    """
    np.save(filepath, data)


def nc_read(filepath, dataset_name):
    """function to read in pixel labels in the NETCDF4 (.nc) format

    Args:
        filepath: string for the filepath to the output file for the pixel labels
        dataset_name: the name of the dataset saved in the file

    Rerturns:
        a numpy array of the output pixel labels
    """
    ds = xr.open_dataset(filepath)
    data = ds[dataset_name].values
    ds.close()
    return data


def nc_write(filepath, dataset_name, data):
    """function to write pixel labels to a NETCDF4 (.nc) formatted file

    Args:
        filepath: string for the filepath to the output file for the pixel labels
        dataset_name: the name of the dataset saved in the file
        data: a numpy array of shape (HEIGHT, WIDTH)
    """
    da = xr.DataArray(data, dims=("y", "x"), name=dataset_name)
    ds = xr.Dataset({dataset_name: da})
    ds.to_netcdf(filepath)


def hdf_read(filepath, dataset_name):
    """function to read in pixel labels in the HDF5 (.h5) format

    Args:
        filepath: string for the filepath to the output file for the pixel labels
        dataset_name: the name of the dataset saved in the file

    Rerturns:
        a numpy array of the output pixel labels
    """
    h5_dataset = h5.File(filepath, "r")
    data = h5_dataset[dataset_name][:]
    h5_dataset.close()
    return data


def hdf_write(filepath, dataset_name, data):
    """function to write pixel labels to a HDF5 (.h5) formatted file

    Args:
        filepath: string for the filepath to the output file for the pixel labels
        dataset_name: the name of the dataset saved in the file
        data: a numpy array of shape (HEIGHT, WIDTH)
    """
    out_file = h5.File(filepath, "w")
    h5_dataset = out_file.create_dataset(dataset_name, data=data)
    out_file.close()


def format_scene_label_file(filepath):
    """
    formats filepath string to replace sub-string '<view>' with 'ALL' for the purpose of output files for all
    multi-angle views, for a multi-angular imager. 
    """
    return f'{os.path.splitext(filepath)[0]}_scenelabels.json'.replace(
        "<view>", "ALL")


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
    if os.path.exists(filepath):
        old_scene_attributes = scene_labels_read(filepath)
        for key, value in scene_attributes.items():
            old_scene_attributes[key] = value
        scene_attributes = old_scene_attributes
    with open(filepath, "w") as json_file:
        json.dump(scene_attributes, json_file, indent=4)


def check_file_exists(filepath):
    """
        Checks to see if a filepath exists for the purpose of reading in pixel labels from prior editing
    """
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
    """ read in prior iteration of various output files generated by the user

    Args:
        output_filepath: pixel label output filepath string, with '<view>' sub-string 
        dataset_name: the name of the dataset saved in the file
        views: list of strings representing diferent views for a multi-angle imager
        review_filepath: filepath to the CSV file for review/evaluation of various scenes
        scene_attrs: boolean stating whether to attempt to read-in the scene labels file

    Returns:
        labels: a numpy array of the prior manual pixel labels read in with a shape (HEIGHT, WIDTH, NUMBER OF VIEWS)
        scene_attributes: a dict of the scene label variables and the corresponding values 
        review_grade: int number representing the quality of the operational labels (typically values 1-5)
        review_status: string representing whether this scene is 'Ungraded'  'Accepted' or 'Rejected' 
        notes: a string of the user's prior notes
    """
    # Read in the scene labels
    if scene_attrs:
        # TODO check scene_attrs load vs. what is passed... they may differ and is not accounted for
        scene_label_filepath = format_scene_label_file(output_filepath)
        check_file_exists(scene_label_filepath)
        scene_attributes = scene_labels_read(scene_label_filepath)
        notes = scene_attributes.pop('notes', None)
        if notes == '':
            notes = None
    else:
        scene_attributes = None
        notes = None

    # Read in review grade if it exists, if not, load as 'None'
    if review_filepath:
        df = pd.read_csv(review_filepath)
        df = df[df['filename'] == output_filepath]
        if len(df) > 0:
            review_grade = df['cloud_mask_grade'][0]
            review_status = df['cloud_mask_status'][0]
    try:
        review_grade
        review_status
    except:
        review_grade = None
        review_status = None

    # Open prior pixel labels created by the user
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

    return labels, scene_attributes, review_grade, review_status, notes
