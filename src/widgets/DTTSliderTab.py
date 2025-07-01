from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSlider,
    QPushButton,
    QCheckBox,
)
from qtpy.QtCore import Qt


class DTTSliderTab(QWidget):
    """Tab widget with vertical sliders for each DTT layer."""

    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.sliders = {}
        self.text_boxes = {}
        self.slider_range = (-101, 101)
        self.view_values = {}
        self.current_view = (self.viewer.dims.current_step[0]
                             if self.viewer.dims.ndim > 0 else 0)

        main_layout = QHBoxLayout()
        sliders_layout = QHBoxLayout()
        sliders_layout.setSpacing(15)

        for layer in self.viewer.layers:
            if layer.name.startswith("DTT"):
                layer_layout = QHBoxLayout()
                layer_layout.setSpacing(5)

                slider = QSlider(Qt.Vertical)
                slider.setRange(*self.slider_range)
                slider.setValue(0)
                slider.valueChanged.connect(self._slider_changed)

                info_layout = QVBoxLayout()
                label = QLabel(layer.name)
                label.setAlignment(Qt.AlignCenter)
                text = QLineEdit("0")
                text.setFixedWidth(50)
                text.editingFinished.connect(self._text_changed)
                info_layout.addWidget(label)
                info_layout.addWidget(text)

                layer_layout.addWidget(slider)
                layer_layout.addLayout(info_layout)

                sliders_layout.addLayout(layer_layout)
                self.sliders[layer.name] = slider
                self.text_boxes[layer.name] = text

        # Layout for button and checkbox on the right
        button_layout = QVBoxLayout()
        self.save_all_checkbox = QCheckBox("Save All Views Configs")
        button_layout.addWidget(self.save_all_checkbox)

        btn = QPushButton("Generate Config File\nSave Cloud Mask")
        btn.setFixedWidth(120)
        btn.setFixedHeight(80)
        btn.clicked.connect(self.print_values)
        button_layout.addWidget(btn)

        main_layout.addLayout(sliders_layout, stretch=9)
        main_layout.addLayout(button_layout, stretch=1)
        self.setLayout(main_layout)

        # Connect view change event to sync slider values
        self.viewer.dims.events.current_step.connect(self._view_changed)

    def _slider_changed(self, value):
        slider = self.sender()
        for name, s in self.sliders.items():
            if s is slider:
                self.text_boxes[name].setText(str(value))
                self.view_values.setdefault(self.current_view, {})[name] = value
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
                value = max(self.slider_range[0], min(self.slider_range[1], value))
                self.sliders[name].setValue(int(value))
                self.view_values.setdefault(self.current_view, {})[name] = int(value)
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
