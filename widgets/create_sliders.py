from widgets.SelectionMinMaxSlider import SelectionMinMaxSlider
from widgets.LayerMinMaxSlider import LayerMinMaxSlider
from qtpy.QtWidgets import QVBoxLayout, QWidget, QSlider, QLabel, QScrollArea, QFrame
import numpy as np


def create_sliders(option, viewer, layers, data, band_names, area='right'):

    if option == 0:
        return None
    elif option == 1:
        slider_widget = SelectionMinMaxSlider(viewer)
        return slider_widget, slider_widget
    elif option == 2:
        sliders = []
        layout = QVBoxLayout()
        for i, layer in enumerate(layers):
            if band_names[i] != "No Retrieval":
                slider_widget = LayerMinMaxSlider(
                    layer,
                    override_max=np.nanmax(data[:, :, i, :]),
                    override_min=np.nanmin(data[:, :, i, :]))
                layout.addWidget(slider_widget)
                sliders.append(slider_widget)

        container = QWidget()
        container.setLayout(layout)

        scroll_area_widget = QScrollArea()
        scroll_area_widget.setWidgetResizable(True)
        scroll_area_widget.setWidget(container)

        return sliders, scroll_area_widget
