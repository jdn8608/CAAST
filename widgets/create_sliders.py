
from widgets.DynamicMinMaxSlider import MinMaxSlider as DMMS

def create_sliders(option, viewer, area='right'):
	
	if option == 0:
		return
	elif option == 1:
		slider_widget = DMMS(viewer)
		viewer.window.add_dock_widget(slider_widget, name="Min-Max Range Slider", area=area)

