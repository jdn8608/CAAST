"""Widget to display histograms for gray-band layers."""

import numpy as np
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QCheckBox,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from util.LayerType import LayerType


class HistogramTab(QWidget):
    """Tab widget showing histograms for all gray-band layers."""

    def __init__(self, viewer, layer_manager):
        super().__init__()
        self.viewer = viewer
        self.layer_manager = layer_manager

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Matplotlib canvas for histograms
        self.figure = Figure(figsize=(4, 3))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Controls for histogram options
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Bins:"))
        self.bin_spin = QSpinBox()
        self.bin_spin.setRange(1, 512)
        self.bin_spin.setValue(50)
        self.bin_spin.valueChanged.connect(self._trigger_update)
        controls.addWidget(self.bin_spin)

        self.log_check = QCheckBox("Log Scale")
        self.log_check.stateChanged.connect(self._trigger_update)
        controls.addWidget(self.log_check)
        controls.addStretch()

        layout.addLayout(controls)

    def _trigger_update(self):
        """Helper to update histograms for the current view."""
        view_idx = self.viewer.dims.current_step[0]
        self.update_histograms(view_idx)

    def _get_gray_layers(self):
        group = self.layer_manager.groups.get(LayerType.GRAY_BAND.value)
        if not group:
            return []
        return [layer for layer, _ in group.get("layers", [])]

    def update_histograms(self, view_idx):
        """Compute and display histograms for all gray-band layers."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        layers = self._get_gray_layers()
        bins = self.bin_spin.value()
        use_log = self.log_check.isChecked()

        for layer in layers:
            data = layer.data[view_idx]
            data = data[np.isfinite(data)]
            if data.size == 0:
                continue
            ax.hist(
                data.ravel(),
                bins=bins,
                histtype="step",
                label=layer.name,
                log=use_log,
            )

        if layers:
            ax.legend(fontsize="small")
        ax.set_xlabel("Value")
        ax.set_ylabel("Frequency")
        if use_log:
            ax.set_yscale("log")
        else:
            ax.set_yscale("linear")

        self.canvas.draw_idle()
