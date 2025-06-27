import napari
from qtpy.QtWidgets import (QFrame, QGridLayout, QSlider, QSpinBox, QLineEdit,
                            QPushButton, QLabel, QComboBox, QSizePolicy)
from qtpy.QtCore import Qt, QPoint

from qtpy.QtGui import QColor, QImage, QPixmap, QIcon
# Custom dual-slider for contrast
from superqt import QRangeSlider  # Replaces napari internal import

import numpy as np


class ControlPanel(QFrame):

    def __init__(self, main_viewer, viewers):
        super().__init__()

        self.main_viewer = main_viewer
        self.viewers = viewers

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

        # Colormap selection for image and label layers
        self.colormap_label = QLabel("Colormap:")
        self.colormap_dropdown = QComboBox()
        self.colormap_dropdown.currentIndexChanged.connect(
            self.change_colormap)
        self.colormap_preview = QLabel()
        self.colormap_preview.setFixedHeight(20)
        self.colormap_preview.setMinimumWidth(100)

        # Populate the dropdown with napari's built-in colormaps along with
        # any custom colormaps defined in ``util/colormaps.py``.
        from util.colormaps import list_all_colormap_names

        self._colormap_options = list_all_colormap_names()

        for cmap in self._colormap_options:
            icon = self._create_colormap_icon(cmap)
            self.colormap_dropdown.addItem(icon, cmap)

        self.control_layout.addWidget(self.colormap_label, 12, 0)
        self.control_layout.addWidget(self.colormap_dropdown, 12, 1)
        self.control_layout.addWidget(self.colormap_preview, 13, 0, 1, 2)

        self.update_labels_btn = QPushButton("Update Viewers")
        self.update_labels_btn.clicked.connect(self.update_viewer_labels)
        self.control_layout.addWidget(self.update_labels_btn, 14, 0, 1, 2)

        self.update_tool_visibility()
        self.main_viewer.layers.selection.events.active.connect(
            lambda e: self.update_tool_visibility())

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

    def update_tool_visibility(self):
        layer = self.main_viewer.layers.selection.active
        is_labels = layer and layer._type_string == 'labels'
        if is_labels is None:
            is_labels = False
        is_image = layer and layer._type_string == 'image'
        if is_image is None:
            is_image = False

        self.paint_button.setVisible(is_labels)
        self.fill_button.setVisible(is_labels)
        self.erase_button.setVisible(is_labels)
        self.pick_button.setVisible(is_labels)
        self.polygon_button.setVisible(is_labels)
        self.brush_size_slider.setVisible(is_labels)
        self.label_controls_label.setVisible(is_labels)
        self.label_spin.setVisible(is_labels)
        self.label_color.setVisible(is_labels)
        self.brush_size_label.setVisible(is_labels)

        self.contrast_slider.setVisible(is_image)
        self.contrast_slider_label.setVisible(is_image)
        self.min_textbox.setVisible(is_image)
        self.max_textbox.setVisible(is_image)

        self.opacity_slider.setVisible(is_labels or is_image)
        self.opacity_label.setVisible(is_labels or is_image)
        self.colormap_label.setVisible(is_labels or is_image)
        self.colormap_dropdown.setVisible(is_labels or is_image)
        self.colormap_preview.setVisible(is_labels or is_image)

        if is_labels:
            self.update_label_color()
            self.label_spin.setValue(layer.selected_label or 0)
            self.brush_size_slider.setValue(layer.brush_size)
        if is_labels or is_image:
            self.opacity_slider.setValue(int(layer.opacity * 100))
            self._sync_colormap_dropdown(layer)
        if is_image:
            self.update_contrast_slider(layer)

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
                layer = self.main_viewer.layers.selection.active
                if layer and layer._type_string == 'image':
                    layer.contrast_limits = (min_val, max_val)
                    self.update_contrast_slider(layer)
        except ValueError:
            pass

    def set_contrast_limits(self):
        active_layer = self.main_viewer.layers.selection.active
        if active_layer and active_layer._type_string == 'image':
            smin, smax = self.contrast_slider.value()
            data_min, data_max = self._contrast_data_min, self._contrast_data_max
            fmin = data_min + (smin / self._slider_steps) * (data_max -
                                                             data_min)
            fmax = data_min + (smax / self._slider_steps) * (data_max -
                                                             data_min)
            if fmin < fmax:
                active_layer.contrast_limits = (fmin, fmax)
                self.min_textbox.setText(f"{fmin:.4g}")
                self.max_textbox.setText(f"{fmax:.4g}")

    def update_label_color(self):
        active_layer = self.main_viewer.layers.selection.active
        if active_layer and active_layer._type_string == 'labels':
            label = active_layer.selected_label
            color = active_layer.get_color(label)
            if color is None:
                color = [1., 1., 1.]
            self.label_color.setStyleSheet(
                f"background-color: rgba({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)}, 255);"
            )

    def set_brush_size(self):
        active_layer = self.main_viewer.layers.selection.active
        if active_layer and active_layer._type_string == 'labels':
            active_layer.brush_size = self.brush_size_slider.value()

    def set_opacity(self):
        active_layer = self.main_viewer.layers.selection.active
        if active_layer and active_layer._type_string in ['labels', 'image']:
            active_layer.opacity = self.opacity_slider.value() / 100

    def change_colormap(self):
        layer = self.main_viewer.layers.selection.active
        if not layer:
            return

        cmap_name = self.colormap_dropdown.currentText()
        from napari.utils.colormaps import AVAILABLE_COLORMAPS
        from util.colormaps import get_colormap

        if layer._type_string == 'labels':
            # Labels expect a discrete mapping dictionary
            layer.colormap = get_colormap(cmap_name)
        elif layer._type_string == 'image':
            # Images expect a continuous Colormap.  Use napari's built-in map if available
            if cmap_name in AVAILABLE_COLORMAPS:
                layer.colormap = AVAILABLE_COLORMAPS[cmap_name]
            else:
                layer.colormap = cmap_name
        self._update_colormap_preview(cmap_name)

    def _create_colormap_icon(self, cmap_name, width=100, height=20):
        """Return a QIcon preview for the provided colormap name or mapping."""
        from napari.utils.colormaps import AVAILABLE_COLORMAPS
        import matplotlib.cm as cm
        from matplotlib.colors import to_rgb
        from util.colormaps import get_colormap

        # Resolve custom maps or direct dictionary input
        if isinstance(cmap_name, dict):
            cmap_dict = cmap_name
        elif isinstance(cmap_name, str) and cmap_name.startswith('custom_'):
            cmap_dict = get_colormap(cmap_name)
        else:
            cmap_dict = None

        if cmap_dict is not None:
            ordered = [cmap_dict[k][:3] for k in sorted(cmap_dict.keys())]
            colors = np.array(ordered)
            if len(colors) < width:
                colors = np.repeat(colors, int(np.ceil(width / len(colors))), axis=0)
            colors = colors[:width]
        else:
            name = str(cmap_name)
            if name in AVAILABLE_COLORMAPS:
                cmap = AVAILABLE_COLORMAPS[name]
                gradient = cmap.map(np.linspace(0, 1, width))
                colors = gradient[:, :3]
            else:
                try:
                    cmap = cm.get_cmap(name)
                    gradient = np.linspace(0, 1, width)
                    colors = cmap(gradient)[:, :3]
                except ValueError:
                    try:
                        single = to_rgb(name)
                    except ValueError:
                        single = (0.5, 0.5, 0.5)
                    colors = np.tile(single, (width, 1))

        colors = (colors * 255).astype(np.uint8)
        img = np.repeat(colors[None, ...], height, axis=0)
        image = QImage(img.data, width, height, 3 * width, QImage.Format_RGB888)
        return QIcon(QPixmap.fromImage(image.copy()))

    def _update_colormap_preview(self, cmap_name):
        icon = self._create_colormap_icon(cmap_name, width=300)
        self.colormap_preview.setPixmap(
            icon.pixmap(self.colormap_preview.size()))

    def _sync_colormap_dropdown(self, layer):
        from util.colormaps import get_colormap

        cmap_obj = layer.colormap
        if hasattr(cmap_obj, 'name'):
            cmap_name = cmap_obj.name
        else:
            cmap_name = None
            for name in self._colormap_options:
                if name.startswith('custom_') and isinstance(cmap_obj, dict) and cmap_obj == get_colormap(name):
                    cmap_name = name
                    break
            if cmap_name is None:
                cmap_name = str(cmap_obj)
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
