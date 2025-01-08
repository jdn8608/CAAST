import napari
import numpy as np
from magicgui import widgets
from qtpy.QtWidgets import QVBoxLayout, QLabel, QWidget, QHBoxLayout
from qtpy.QtGui import QColor, QPixmap
from qtpy.QtCore import Qt


# Function to create a color square for the legend
def create_color_square(color):
    pixmap = QPixmap(20, 20)
    color_rgb = tuple(int(255 * c)
                      for c in color)  # Convert to 0-255 RGB for QColor
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


def create_legend(label_colormap, label_mapping):
    height = 30 * len(list(label_mapping.keys()))
    width = 250
    legend_widget = LegendWidget(label_colormap, label_mapping)
    legend_widget.setMaximumWidth(width)
    legend_widget.setMaximumHeight(height)
    return legend_widget, width, height
