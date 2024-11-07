import napari
import numpy as np
from magicgui import widgets
from qtpy.QtWidgets import QVBoxLayout, QLabel, QWidget, QHBoxLayout
from qtpy.QtGui import QColor, QPixmap
from qtpy.QtCore import Qt

# Function to create a color square for the legend
def create_color_square(color):
    pixmap = QPixmap(20, 20)
    color_rgb = tuple(int(255 * c) for c in color)  # Convert to 0-255 RGB for QColor
    pixmap.fill(QColor(*color_rgb))
    return pixmap

# Create a legend widget
class LegendWidget(QWidget):
    def __init__(self, colormap, label_mapping):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        
        # Populate the legend with color and labels
        for label_value, color in colormap.items():
            row_layout = QHBoxLayout()
            
            # Color box
            color_label = QLabel()
            color_label.setPixmap(create_color_square(color))
            row_layout.addWidget(color_label)
            
            # Label with number and description
            label_text = QLabel(f"{label_value}: {label_mapping[label_value]}")
            row_layout.addWidget(label_text)
            
            layout.addLayout(row_layout)
        
        self.setLayout(layout)

def create_legend(viewer, label_colormap, label_mapping, area='left'):
	legend_widget = LegendWidget(label_colormap, label_mapping)
	legend_widget.setMaximumWidth(250)
	legend_widget.setMaximumHeight(30*len(list(label_mapping.keys())))
	viewer.window.add_dock_widget(legend_widget, area=area, name="Legend")
	

	if area == 'left':	
		layer_list_dock = viewer.window._qt_viewer.dockLayerList
		print(help(layer_list_dock))
		layer_controls_dock = viewer.window._qt_viewer.dockLayerControls
		layer_controls_dock.setMaximumWidth(250)
		layer_controls_dock.setMaximumHeight(400)
		layer_list_dock.setMaximumWidth(250)
		viewer.window.add_dock_widget(layer_controls_dock, area=area)
		viewer.window.add_dock_widget(layer_list_dock, area=area)






