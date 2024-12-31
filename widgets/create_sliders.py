from widgets.SelectionMinMaxSlider import SelectionMinMaxSlider
from widgets.LayerMinMaxSlider import LayerMinMaxSlider
from qtpy.QtWidgets import QVBoxLayout, QWidget, QSlider, QLabel, QScrollArea, QFrame
import numpy as np


def create_sliders(option, viewer, layers, data):
    """ creates and returns slider(s) (either Selection or Layer-based sliders) to be added to a napari viewer

    Args:
        option : an integer to select which kind of slider to create for the tool
        viewer : a pointer to the napari viewer object (only to be referenced by the Selection Slider widget) 
        layers : band layers from the instrument to allow slider functionality for
        data : the NumPy data array for the band data

    Returns:
        slider_widget : object of the slider widget created
        scroll_area_widget : the scroll widget contained for the LayerSliders (if used)
    """

    # Create a min/max selection slider
    if option == 1:
        slider_widget = SelectionMinMaxSlider(viewer)
        return slider_widget, slider_widget
    # Create a min/max slider for each band
    elif option == 2:
        sliders = []
        layout = QVBoxLayout()
        for i, layer in enumerate(layers):
            slider_widget = LayerMinMaxSlider(
                layer,
                override_max=np.nanmax(data[:, :, i, :]),
                override_min=np.nanmin(data[:, :, i, :]))
            layout.addWidget(slider_widget)
            sliders.append(slider_widget)

        # Add the sliders to a scrollable widget (if they don't all fit on screen)
        container = QWidget()
        container.setLayout(layout)

        scroll_area_widget = QScrollArea()
        scroll_area_widget.setWidgetResizable(True)
        scroll_area_widget.setWidget(container)

        return sliders, scroll_area_widget
    else:
        return None, None
