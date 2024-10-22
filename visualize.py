import tqdm 
import numpy as np
import napari 


def single_view_multi_band(data, band_names, prior_labels=False):
	viewer = napari.Viewer()
	viewer.add_image(data, name=band_names, channel_axis=2, contrast_limits=(0,1), colormap='gray')

	if prior_labels:
		mask_colormap = {
         		0: [1.0,1.0,1.0,1.0],
          		1: [0.0,0.0,0.0,0.0],
          		3: [1.0,0.0,0.0,1.0]
  			}	

		labels_layer = viewer.add_labels(data[:,:,-1].astype(int), name='Manual Label', colormap=mask_colormap)

	napari.run()
	viewer.close()



def multi_view_multi_band(data, band_names, prior_labels=False):
	viewer = napari.Viewer()
	viewer.add_image(data, name=band_names, channel_axis=2, colormap='gray')

	if prior_labels:
		mask_colormap = {
         		0: [1.0,1.0,1.0,1.0],
          		1: [0.0,0.0,0.0,0.0],
          		3: [1.0,0.0,0.0,1.0]
  			}	

		labels_layer = viewer.add_labels(output[:,:,-1].astype(int), name='Labeling', colormap=colormap)

	napari.run()
	viewer.close()
