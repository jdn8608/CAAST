from widgets.SelectionMinMaxSlider import SelectionMinMaxSlider
from widgets.LayerMinMaxSlider import LayerMinMaxSlider

def create_sliders(option, viewer, layers=None, band_names=None, area='right'):
	
	if option == 0:
		return None
	elif option == 1:
		slider_widget = SelectionMinMaxSlider(viewer)
		viewer.window.add_dock_widget(slider_widget, name="Min-Max Range Slider", area=area)
		return slider_widget
	elif option == 2:
		sliders = []
		for i, layer in enumerate(layers):
			if band_names[i] != "No Retrieval":
				slider_widget = LayerMinMaxSlider(layer)
				viewer.window.add_dock_widget(slider_widget, name=band_names[i], area=area)
				sliders.append(slider_widget)
		return sliders


