from qtpy.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSlider, QPushButton
from qtpy.QtCore import Qt


class DTTSliderTab(QWidget):
    """Tab widget with vertical sliders for each DTT layer."""

    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.sliders = {}
        self.text_boxes = {}
        self.slider_range = (-100, 100)

        main_layout = QVBoxLayout()
        sliders_layout = QHBoxLayout()

        for layer in self.viewer.layers:
            if layer.name.startswith("DTT"):
                vbox = QVBoxLayout()
                label = QLabel(layer.name)
                label.setAlignment(Qt.AlignCenter)
                slider = QSlider(Qt.Vertical)
                slider.setRange(*self.slider_range)
                slider.setValue(0)
                slider.valueChanged.connect(self._slider_changed)
                text = QLineEdit("0")
                text.editingFinished.connect(self._text_changed)
                vbox.addWidget(label)
                vbox.addWidget(slider, stretch=1)
                vbox.addWidget(text)
                sliders_layout.addLayout(vbox)
                self.sliders[layer.name] = slider
                self.text_boxes[layer.name] = text

        main_layout.addLayout(sliders_layout)
        btn = QPushButton("Generate Config File and Save Cloud Mask")
        btn.clicked.connect(self.print_values)
        main_layout.addWidget(btn)
        self.setLayout(main_layout)

    def _slider_changed(self, value):
        slider = self.sender()
        for name, s in self.sliders.items():
            if s is slider:
                self.text_boxes[name].setText(str(value))
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
                break
        self.print_values()

    def print_values(self):
        values = {name: slider.value() for name, slider in self.sliders.items()}
        print("Current DTT slider values:", values)
