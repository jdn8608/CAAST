import napari
from qtpy.QtWidgets import (QFrame, QGridLayout, QSlider, QSpinBox, QLineEdit,
                            QPushButton, QLabel, QComboBox, QSizePolicy)
from qtpy.QtCore import Qt, QPoint

from qtpy.QtGui import QColor, QImage, QPixmap, QIcon
import json
from util.colormaps import build_label_colormap
# Custom dual-slider for contrast
from superqt import QRangeSlider  # Replaces napari internal import

import numpy as np


class ControlPanel(QFrame):

    def __init__(self, main_viewer, viewers):
        super().__init__()

        self.main_viewer = main_viewer
        self.viewers = viewers

        # Keep track of the layers the panel should operate on. By default this
        # is just the currently selected layer in the main viewer, but can be
        # overridden (e.g. when a group is selected).
        self.active_layers = []

        self._contrast_data_min = 0.0
        self._contrast_data_max = 1.0
        self._slider_steps = 1000

        # Create the grid layout
        self.setFixedWidth(300)
        self.control_layout = QGridLayout()
        self.setLayout(self.control_layout)

        # Add text indicator on what mode is active
        self.mode_label = QLabel("Current Mode: pan_zoom")
        self.control_layout.addWidget(self.mode_label, 0, 0, 1, 2)

        # Create, Add, and Connect buttons for mode selection
        self.pan_button = QPushButton("Pan/Zoom [Z]")
        self.pan_button.clicked.connect(
            lambda: self.set_viewer_mode("pan_zoom"))
        self.paint_button = QPushButton("Paint [P]")
        self.paint_button.clicked.connect(
            lambda: self.set_viewer_mode("paint"))
        self.fill_button = QPushButton("Fill [F]")
        self.fill_button.clicked.connect(lambda: self.set_viewer_mode("fill"))
        self.erase_button = QPushButton("Erase [E]")
        self.erase_button.clicked.connect(
            lambda: self.set_viewer_mode("erase"))
        self.pick_button = QPushButton("Pick [L]")
        self.pick_button.clicked.connect(lambda: self.set_viewer_mode("pick"))
        self.polygon_button = QPushButton("Draw Polygon [3]")
        self.polygon_button.clicked.connect(
            lambda: self.set_viewer_mode("draw_polygon"))

        self.paint_button.setSizePolicy(QSizePolicy.Expanding,
                                        QSizePolicy.Preferred)
        self.fill_button.setSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Preferred)
        self.erase_button.setSizePolicy(QSizePolicy.Expanding,
                                        QSizePolicy.Preferred)
        self.pick_button.setSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Preferred)

        self.control_layout.addWidget(self.pan_button, 1, 0, 1, 2)
        self.control_layout.addWidget(self.paint_button, 2, 0, 1, 1)
        self.control_layout.addWidget(self.fill_button, 2, 1, 1, 1)
        self.control_layout.addWidget(self.erase_button, 3, 0)
        self.control_layout.addWidget(self.pick_button, 3, 1)
        self.control_layout.addWidget(self.polygon_button, 4, 0, 1, 2)

        # Label Selection
        self.label_controls_label = QLabel("Label:")
        self.label_spin = QSpinBox()
        self.label_spin.setRange(0, 255)
        self.label_spin.valueChanged.connect(self.set_label_value)
        self.label_color = QLabel()
        self.label_color.setFixedSize(20, 20)
        self.label_color.setStyleSheet("background: gray")

        self.control_layout.addWidget(self.label_controls_label, 5, 0)
        self.control_layout.addWidget(self.label_spin, 5, 1)
        self.control_layout.addWidget(self.label_color, 6, 0, 1, 2)

        self.brush_size_label = QLabel("Brush Size:")
        self.brush_size_slider = QSlider(Qt.Horizontal)
        self.brush_size_slider.setRange(1, 100)
        self.brush_size_slider.setValue(10)
        self.brush_size_slider.valueChanged.connect(self.set_brush_size)
        self.control_layout.addWidget(self.brush_size_label, 7, 0)
        self.control_layout.addWidget(self.brush_size_slider, 7, 1)

        self.opacity_label = QLabel("Opacity:")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.set_opacity)
        self.control_layout.addWidget(self.opacity_label, 8, 0)
        self.control_layout.addWidget(self.opacity_slider, 8, 1)

        self.contrast_slider_label = QLabel("Contrast:")
        self.contrast_slider = QRangeSlider(Qt.Horizontal)
        self.contrast_slider.setRange(0, self._slider_steps)
        self.contrast_slider.setValue((0, self._slider_steps))
        self.contrast_slider.valuesChanged.connect(self.set_contrast_limits)
        self.control_layout.addWidget(self.contrast_slider_label, 9, 0)
        self.control_layout.addWidget(self.contrast_slider, 10, 0, 1, 2)
        self.min_textbox = QLineEdit()
        self.min_textbox.setPlaceholderText("Min")
        self.min_textbox.returnPressed.connect(self.update_contrast_from_text)
        self.control_layout.addWidget(self.min_textbox, 11, 0)
        self.max_textbox = QLineEdit()
        self.max_textbox.setPlaceholderText("Max")
        self.max_textbox.returnPressed.connect(self.update_contrast_from_text)
        self.control_layout.addWidget(self.max_textbox, 11, 1)

        # Colormap selection for image layers
        self.colormap_label = QLabel("Colormap:")
        self.colormap_dropdown = QComboBox()
        self.colormap_dropdown.currentIndexChanged.connect(
            self.change_colormap)
        self.colormap_preview = QLabel()
        self.colormap_preview.setFixedHeight(20)
        self.colormap_preview.setMinimumWidth(100)

        # Default list of colormaps.  Start with the common grayscale and diverging
        # options, then extend with the perceptually uniform sets and a few other
        # popular maps.
        self._colormap_options = [
            "gray",
            "gray_r",
            "bwr",
            # Perceptually uniform colormaps
            "viridis",
            "plasma",
            "inferno",
            "magma",
            "cividis",
            # Additional requests
            "Greens",
            "jet",
            "hot",
            "PRGn",
            "gist_rainbow",
            "gist_ncar",
        ]
        for cmap in self._colormap_options:
            icon = self._create_colormap_icon(cmap)
            self.colormap_dropdown.addItem(icon, cmap)

        self.control_layout.addWidget(self.colormap_label, 12, 0)
        self.control_layout.addWidget(self.colormap_dropdown, 12, 1)
        self.control_layout.addWidget(self.colormap_preview, 13, 0, 1, 2)

        # Colormap selection for label layers
        self.label_colormap_label = QLabel("Label Colormap:")
        self.label_colormap_dropdown = QComboBox()
        self.label_colormap_dropdown.currentIndexChanged.connect(
            self.change_label_colormap)
        self.label_colormap_preview = QLabel()
        self.label_colormap_preview.setFixedHeight(20)
        self.label_colormap_preview.setMinimumWidth(100)

        # Populate default label colormap list
        self._label_colormap_options = [
            "random",
            "viridis",
            "tab20",
            "nipy_spectral",
            "tab10",
            "tab20b",
            "tab20c",
            "Set1",
            "Pastel1",
            "Pastel2",
        ]
        try:
            with open('./settings/custom_colormaps.json', 'r') as f:
                for name in json.load(f).keys():
                    self._label_colormap_options.append(f"custom_{name}")
        except Exception:
            pass
        for cmap in self._label_colormap_options:
            icon = self._create_label_colormap_icon(cmap)
            self.label_colormap_dropdown.addItem(icon, cmap)

        self.control_layout.addWidget(self.label_colormap_label, 14, 0)
        self.control_layout.addWidget(self.label_colormap_dropdown, 14, 1)
        self.control_layout.addWidget(self.label_colormap_preview, 15, 0, 1, 2)

        self.update_labels_btn = QPushButton("Update Viewers")
        self.update_labels_btn.clicked.connect(self.update_viewer_labels)
        self.control_layout.addWidget(self.update_labels_btn, 16, 0, 1, 2)

        self.update_tool_visibility()
        self.main_viewer.layers.selection.events.active.connect(
            lambda e: self.update_tool_visibility())

    def set_target_layers(self, layers):
        """Set the layers that should be modified by the control panel."""
        self.active_layers = layers if layers is not None else []
        self.update_tool_visibility(layers)

    def update_viewer_labels(self):
        active_layer = self.main_viewer.layers.selection.active
        if not active_layer or active_layer._type_string != 'labels':
            return
        main_labels = active_layer

        for viewer in self.viewers:
            if viewer is self.main_viewer:
                continue
            for layer in viewer.layers:
                if layer._type_string == 'labels' and layer.name == main_labels.name:
                    layer.data = main_labels.data.copy()

    #function for layer controls
    def set_viewer_mode(self, mode: str):
        if mode in [
                "pan_zoom", "paint", "fill", "erase", "pick", "draw_polygon"
        ]:
            active_layer = self.main_viewer.layers.selection.active
            if not active_layer or active_layer._type_string != 'labels':
                self.mode_label.setText(
                    f"Cannot use '{mode}' on non-labels layer")
                return
            try:
                if mode == "draw_polygon":
                    active_layer.mode = "polygon"
                else:
                    active_layer.mode = mode
            except AttributeError:
                self.mode_label.setText(
                    f"Cannot set mode '{mode}' on active layer.")
                return

            self.mode_label.setText(f"Current Mode: {mode}")

        else:
            print("Unvalid Mode Selected")

    def update_tool_visibility(self, layers=None):
        if layers is None:
            layer = self.main_viewer.layers.selection.active
            self.active_layers = [layer] if layer else []
        else:
            self.active_layers = list(layers)

        if self.active_layers:
            is_labels = all(l._type_string == 'labels' for l in self.active_layers)
            is_image = all(l._type_string == 'image' for l in self.active_layers)
            layer = self.active_layers[0]
        else:
            is_labels = False
            is_image = False
            layer = None

        is_single_labels = is_labels and len(self.active_layers) == 1
        is_single_image = is_image and len(self.active_layers) == 1

        self.paint_button.setVisible(is_single_labels)
        self.fill_button.setVisible(is_single_labels)
        self.erase_button.setVisible(is_single_labels)
        self.pick_button.setVisible(is_single_labels)
        self.polygon_button.setVisible(is_single_labels)
        self.brush_size_slider.setVisible(is_single_labels)
        self.label_controls_label.setVisible(is_single_labels)
        self.label_spin.setVisible(is_single_labels)
        self.label_color.setVisible(is_single_labels)
        self.brush_size_label.setVisible(is_single_labels)

        self.contrast_slider.setVisible(is_image)
        self.contrast_slider_label.setVisible(is_image)
        self.min_textbox.setVisible(is_image)
        self.max_textbox.setVisible(is_image)

        self.opacity_slider.setVisible(is_labels or is_image)
        self.opacity_label.setVisible(is_labels or is_image)
        self.colormap_label.setVisible(is_image)
        self.colormap_dropdown.setVisible(is_image)
        self.colormap_preview.setVisible(is_image)
        self.label_colormap_label.setVisible(is_labels)
        self.label_colormap_dropdown.setVisible(is_labels)
        self.label_colormap_preview.setVisible(is_labels)

        if is_single_labels:
            self.update_label_color()
            self.label_spin.setValue(layer.selected_label or 0)
            self.brush_size_slider.setValue(layer.brush_size)
        if is_labels or is_image:
            self.opacity_slider.setValue(int(layer.opacity * 100))
        if is_image:
            self.update_contrast_slider(layer)
            self._sync_colormap_dropdown(layer)
        if is_labels:
            self._sync_label_colormap_dropdown(layer)

    def set_label_value(self):
        active_layer = self.main_viewer.layers.selection.active
        if active_layer and active_layer._type_string == 'labels':
            active_layer.selected_label = self.label_spin.value()
            self.update_label_color()

    def update_contrast_slider(self, layer):
        data_min, data_max = float(np.nanmin(layer.data)), float(
            np.nanmax(layer.data))
        contrast_min, contrast_max = layer.contrast_limits
        self._contrast_data_min = data_min
        self._contrast_data_max = data_max

        def to_slider(val):
            return int(
                (val - data_min) / (data_max - data_min) * self._slider_steps)

        self.contrast_slider.blockSignals(True)
        self.contrast_slider.setRange(0, self._slider_steps)
        self.contrast_slider.setValue(
            (to_slider(contrast_min), to_slider(contrast_max)))
        self.contrast_slider.blockSignals(False)

        self.min_textbox.setText(f"{contrast_min:.4g}")
        self.max_textbox.setText(f"{contrast_max:.4g}")

    def update_contrast_from_text(self):
        try:
            min_val = float(self.min_textbox.text())
            max_val = float(self.max_textbox.text())
            if min_val < max_val:
                for layer in self.active_layers:
                    if layer._type_string == 'image':
                        layer.contrast_limits = (min_val, max_val)
                        self.update_contrast_slider(layer)
        except ValueError:
            pass

    def set_contrast_limits(self):
        if not self.active_layers:
            return
        smin, smax = self.contrast_slider.value()
        data_min, data_max = self._contrast_data_min, self._contrast_data_max
        fmin = data_min + (smin / self._slider_steps) * (data_max - data_min)
        fmax = data_min + (smax / self._slider_steps) * (data_max - data_min)
        if fmin < fmax:
            for layer in self.active_layers:
                if layer._type_string == 'image':
                    layer.contrast_limits = (fmin, fmax)
            self.min_textbox.setText(f"{fmin:.4g}")
            self.max_textbox.setText(f"{fmax:.4g}")

    def update_label_color(self):
        if not self.active_layers:
            return
        layer = self.active_layers[0]
        if layer and layer._type_string == 'labels':
            label = layer.selected_label
            color = layer.get_color(label)
            if color is None:
                color = [1., 1., 1.]
            self.label_color.setStyleSheet(
                f"background-color: rgba({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)}, 255);"
            )

    def set_brush_size(self):
        for layer in self.active_layers:
            if layer._type_string == 'labels':
                layer.brush_size = self.brush_size_slider.value()

    def set_opacity(self):
        for layer in self.active_layers:
            if layer._type_string in ['labels', 'image']:
                layer.opacity = self.opacity_slider.value() / 100

    def change_colormap(self):
        cmap = self.colormap_dropdown.currentText()
        for layer in self.active_layers:
            if layer._type_string == 'image':
                layer.colormap = cmap
                for viewer in self.viewers:
                    if viewer is self.main_viewer:
                        continue
                    for other in viewer.layers:
                        if other._type_string == 'image' and other.name == layer.name:
                            other.colormap = cmap
        self._update_colormap_preview(cmap)

    def _create_colormap_icon(self, cmap_name, width=100, height=20):
        import matplotlib.cm as cm
        cmap = cm.get_cmap(cmap_name)
        gradient = np.linspace(0, 1, width)
        colors = (cmap(gradient)[:, :3] * 255).astype(np.uint8)
        img = np.repeat(colors[None, ...], height, axis=0)
        image = QImage(img.data, width, height, 3 * width,
                       QImage.Format_RGB888)
        return QIcon(QPixmap.fromImage(image.copy()))

    def _update_colormap_preview(self, cmap_name):
        icon = self._create_colormap_icon(cmap_name, width=300)
        self.colormap_preview.setPixmap(
            icon.pixmap(self.colormap_preview.size()))

    def _sync_colormap_dropdown(self, layer):
        cmap_name = getattr(layer.colormap, 'name', str(layer.colormap))
        if cmap_name not in self._colormap_options:
            self._colormap_options.append(cmap_name)
            self.colormap_dropdown.addItem(
                self._create_colormap_icon(cmap_name), cmap_name)
        idx = self.colormap_dropdown.findText(cmap_name)
        if idx != -1:
            self.colormap_dropdown.blockSignals(True)
            self.colormap_dropdown.setCurrentIndex(idx)
            self.colormap_dropdown.blockSignals(False)
        self._update_colormap_preview(cmap_name)

    def change_label_colormap(self):
        cmap_name = self.label_colormap_dropdown.currentText()
        for layer in self.active_layers:
            if layer._type_string == 'labels':
                cmap = build_label_colormap(cmap_name, np.unique(layer.data))
                layer.colormap = cmap
                layer.metadata['label_colormap_name'] = cmap_name
                for viewer in self.viewers:
                    if viewer is self.main_viewer:
                        continue
                    for other in viewer.layers:
                        if other._type_string == 'labels' and other.name == layer.name:
                            other.colormap = cmap
                            other.metadata['label_colormap_name'] = cmap_name
        self._update_label_colormap_preview(cmap_name)
        if self.active_layers and self.active_layers[0]._type_string == 'labels':
            self.update_label_color()

    def _create_label_colormap_icon(self, cmap_name, width=100, height=20):
        cmap = build_label_colormap(cmap_name, range(6))
        colors = [cmap[k] for k in sorted(cmap) if k is not None][:6]
        cell_w = max(1, width // len(colors))
        img = np.zeros((height, cell_w * len(colors), 3), dtype=np.uint8)
        for i, col in enumerate(colors):
            rgb = (np.array(col[:3]) * 255).astype(np.uint8)
            img[:, i * cell_w:(i + 1) * cell_w] = rgb
        image = QImage(img.data, img.shape[1], height, 3 * img.shape[1],
                       QImage.Format_RGB888)
        return QIcon(QPixmap.fromImage(image.copy()))

    def _update_label_colormap_preview(self, cmap_name):
        icon = self._create_label_colormap_icon(cmap_name, width=300)
        self.label_colormap_preview.setPixmap(
            icon.pixmap(self.label_colormap_preview.size()))

    def _sync_label_colormap_dropdown(self, layer):
        cmap_name = layer.metadata.get('label_colormap_name')
        if not cmap_name:
            attr_name = getattr(layer.colormap, 'name', '')
            if attr_name and attr_name != 'custom':
                cmap_name = attr_name
            else:
                cmap_name = 'random'
        if cmap_name not in self._label_colormap_options:
            self._label_colormap_options.append(cmap_name)
            self.label_colormap_dropdown.addItem(
                self._create_label_colormap_icon(cmap_name), cmap_name)
        idx = self.label_colormap_dropdown.findText(cmap_name)
        if idx != -1:
            self.label_colormap_dropdown.blockSignals(True)
            self.label_colormap_dropdown.setCurrentIndex(idx)
            self.label_colormap_dropdown.blockSignals(False)
        self._update_label_colormap_preview(cmap_name)
