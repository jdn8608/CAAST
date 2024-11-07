
from widgets.DynamicMinMaxSlider import MinMaxSlider as DMMS
from widgets.MinMaxSlider import MinMaxSlider as MMS

def create_sliders(option, viewer, layers=None, band_names=None, area='right'):
	
	if option == 0:
		return
	elif option == 1:
		slider_widget = DMMS(viewer)
		viewer.window.add_dock_widget(slider_widget, name="Min-Max Range Slider", area=area)
	elif option == 2:
		for i, layer in enumerate(layers):
			if band_names[i] != "No Retrieval":
				slider_widget = MMS(layer)
				viewer.window.add_dock_widget(slider_widget, name=band_names[i], area=area)


