from qtpy.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit
from qtpy.QtGui import QColor, QPixmap
from qtpy.QtCore import Qt
import numpy as np


class LabelLegendWidget(QWidget):
    """Widget showing a legend for label layers with editable names."""

    def __init__(self, viewer, config):
        super().__init__()
        self.viewer = viewer
        self.config = config or {}
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.layer_dropdown = QComboBox()
        layout.addWidget(self.layer_dropdown)

        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout()
        self.rows_container.setLayout(self.rows_layout)
        layout.addWidget(self.rows_container)
        layout.addStretch()

        self.layer_dropdown.currentIndexChanged.connect(self.update_rows)
        viewer.layers.events.inserted.connect(lambda e: self.refresh_layers())
        viewer.layers.events.removed.connect(lambda e: self.refresh_layers())
        viewer.layers.selection.events.active.connect(lambda e: self.sync_selection())

        self._current_layer = None

        self.refresh_layers()

    def sync_selection(self):
        layer = self.viewer.layers.selection.active
        if layer and layer._type_string == 'labels':
            idx = self.layer_dropdown.findText(layer.name)
            if idx >= 0 and idx != self.layer_dropdown.currentIndex():
                self.layer_dropdown.setCurrentIndex(idx)

    def refresh_layers(self):
        current = self.layer_dropdown.currentText()
        self.layer_dropdown.blockSignals(True)
        self.layer_dropdown.clear()
        for layer in self.viewer.layers:
            if layer._type_string == 'labels':
                self.layer_dropdown.addItem(layer.name)
        idx = self.layer_dropdown.findText(current)
        if idx >= 0:
            self.layer_dropdown.setCurrentIndex(idx)
        self.layer_dropdown.blockSignals(False)
        self.update_rows()

    def update_rows(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        layer_name = self.layer_dropdown.currentText()
        if not layer_name:
            return
        layer = self.viewer.layers[layer_name]
        if self._current_layer is not None:
            try:
                self._current_layer.events.colormap.disconnect(self.update_rows)
                self._current_layer.events.data.disconnect(self.update_rows)
            except Exception:
                pass
        self._current_layer = layer
        layer.events.colormap.connect(self.update_rows)
        layer.events.data.connect(self.update_rows)
        labels = sorted(set(int(x) for x in np.unique(layer.data)))
        if labels:
            start = min(labels)
            end = max(labels)
        else:
            start = end = 0
        label_map = self.config.get('label_strings', {}).get(
            layer.metadata.get('layer_type', layer.name), {})
        for val in range(start, end + 1):
            color = layer.get_color(val)
            if color is None:
                color = (1.0, 1.0, 1.0, 1.0)
            pix = QPixmap(20, 20)
            pix.fill(QColor(*(int(c*255) for c in color[:3])))
            color_label = QLabel()
            color_label.setPixmap(pix)
            num_label = QLabel(str(val))
            text = label_map.get(str(val))
            if text is None:
                if val < 0:
                    text = 'NAN'
                elif layer.metadata.get('layer_type') == 'Surface Ids':
                    text = f'SID {val}'
                else:
                    text = f'Label {val}'
            text_edit = QLineEdit(text)
            row = QHBoxLayout()
            row.addWidget(color_label)
            row.addWidget(num_label)
            row.addWidget(text_edit)
            row_widget = QWidget()
            row_widget.setLayout(row)
            self.rows_layout.addWidget(row_widget)
        self.rows_layout.addStretch()
