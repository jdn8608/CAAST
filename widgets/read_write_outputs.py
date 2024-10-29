import numpy as np
import h5py as h5
import xarray as xr

def save_labels(data, qual_dict, output_filepath, dataset_name):

                filetype = output_filepath.split('.')[-1]
                if qual_dict:
                        qual_attributes = {label: combo_box.currentText() for label, combo_box in qual_dict.items()}
                        print(qual_attributes)

                if filetype == 'npy':
                        np.save(output_filepath, data)
                        if qual_dict:
                                np.save(output_filepath.split('.')[0]+'_qual.npy', qual_attributes)
                elif filetype == 'hdf' or filtype=='hdf5':
                        out_file = h5.File(output_filepath, "w")
                        h5_dataset = out_file.create_dataset(dataset_name, data=data)
                        if qual_dict:
                                for key, value in qual_attributes.items():
                                        h5_dataset.attrs[key] = value
                        out_file.close()
                elif filetype == 'nc':
                        da = xr.DataArray(
                                data,
                                dims=("y", "x"),
                                name=dataset_name
                        )
                        if qual_dict:
                                ds = xr.Dataset({dataset_name: da}, attrs=qual_attributes)
                        else:
                                ds = xr.Dataset({dataset_name:da})
                        ds.to_netcdf(output_filepath)
                else:
                        raise Exception(f"filetype '{filetype}' id not currently supported for saving files.\n please use a different filetype for output, or add functionality for this filetype")
