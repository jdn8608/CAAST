from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSlider,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QFrame,
)
from qtpy.QtCore import Qt


class DTTSliderTab(QWidget):
    """Tab widget with vertical sliders for each DTT layer.

    Parameters
    ----------
    viewer : napari.Viewer
        Viewer instance used to track current view.
    initial_values : dict[int, dict[str, int]], optional
        Mapping of view index to slider values by layer name.
    """

    def __init__(self, viewer, initial_values=None):
        super().__init__()
        self.viewer = viewer
        self.sliders = {}
        self.text_boxes = {}
        self.slider_range = (-101, 101)
        # Storage for slider values per view
        self.view_values = {
            k: dict(v)
            for k, v in (initial_values or {}).items()
        }
        self.current_view = (self.viewer.dims.current_step[0]
                             if self.viewer.dims.ndim > 0 else 0)

        main_layout = QHBoxLayout()
        sliders_layout = QHBoxLayout()
        sliders_layout.setSpacing(80)

        for layer in self.viewer.layers:
            if layer.name.startswith("DTT"):
                layer_layout = QHBoxLayout()
                layer_layout.setSpacing(5)

                slider = QSlider(Qt.Vertical)
                slider.setRange(*self.slider_range)
                start_val = self.view_values.get(self.current_view,
                                                 {}).get(layer.name, 0)
                slider.setValue(start_val)
                slider.valueChanged.connect(self._slider_changed)

                info_layout = QVBoxLayout()
                label = QLabel(layer.name)
                label.setAlignment(Qt.AlignCenter)
                text = QLineEdit(str(start_val))
                text.setFixedWidth(50)
                text.editingFinished.connect(self._text_changed)
                info_layout.addWidget(label)
                info_layout.addWidget(text)

                layer_layout.addWidget(slider)
                layer_layout.addLayout(info_layout)

                sliders_layout.addLayout(layer_layout)
                self.sliders[layer.name] = slider
                self.text_boxes[layer.name] = text
                self.view_values.setdefault(self.current_view,
                                            {})[layer.name] = start_val

        # Layout for radio buttons and button on the right
        button_layout = QVBoxLayout()
        self.radio_group = QButtonGroup(self)
        self.save_current_radio = QRadioButton("Save current view's config")
        self.save_all_radio = QRadioButton("Save all views' config")
        self.radio_group.addButton(self.save_current_radio)
        self.radio_group.addButton(self.save_all_radio)
        self.save_current_radio.setChecked(True)
        button_layout.addWidget(self.save_current_radio)
        button_layout.addWidget(self.save_all_radio)

        btn = QPushButton("Generate Config File\nSave Cloud Mask")
        btn.setFixedWidth(200)
        btn.setFixedHeight(100)
        btn.clicked.connect(self.print_values)
        button_layout.addWidget(btn)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setMidLineWidth(3)
        separator.setLineWidth(3)
        separator.setStyleSheet("color: #323232 ")

        main_layout.addLayout(sliders_layout, stretch=9)
        main_layout.addWidget(separator)
        main_layout.addLayout(button_layout, stretch=1)
        self.setLayout(main_layout)

        # Connect view change event to sync slider values
        self.viewer.dims.events.current_step.connect(self._view_changed)

    def _slider_changed(self, value):
        slider = self.sender()
        for name, s in self.sliders.items():
            if s is slider:
                self.text_boxes[name].setText(str(value))
                self.view_values.setdefault(self.current_view,
                                            {})[name] = value
                break
        self.print_values()

    def _text_changed(self):
        text = self.sender()
        for name, t in self.text_boxes.items():
            if t is text:
                try:
                    value = float(t.text())
                except ValueError:
                    return
                value = max(self.slider_range[0],
                            min(self.slider_range[1], value))
                self.sliders[name].setValue(int(value))
                self.view_values.setdefault(self.current_view,
                                            {})[name] = int(value)
                break
        self.print_values()

    def print_values(self):
        values = self.view_values.get(self.current_view, {})
        print("Current DTT slider values:", values)

    def _save_current_values(self):
        self.view_values.setdefault(self.current_view, {})
        for name, slider in self.sliders.items():
            self.view_values[self.current_view][name] = slider.value()

    def _load_view_values(self):
        values = self.view_values.get(self.current_view, {})
        for name, slider in self.sliders.items():
            val = values.get(name, 0)
            slider.blockSignals(True)
            self.text_boxes[name].blockSignals(True)
            slider.setValue(val)
            self.text_boxes[name].setText(str(val))
            slider.blockSignals(False)
            self.text_boxes[name].blockSignals(False)

    def _view_changed(self, event):
        self._save_current_values()
        self.current_view = self.viewer.dims.current_step[0]
        self._load_view_values()
