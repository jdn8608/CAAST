"""Widget to display smoothed distributions for gray-band layers."""

import numpy as np
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QGroupBox,
    QPushButton,
    QDialog,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.stats import gaussian_kde

from util.LayerType import LayerType


class HistogramTab(QWidget):
    """Tab widget showing distributions for all gray-band layers."""

    def __init__(self, viewer, layer_manager):
        super().__init__()
        self.viewer = viewer
        self.layer_manager = layer_manager

        self.layer_checks = {}
        self.popup = None

        # Main horizontal layout: left plot, middle band checks, right controls
        layout = QHBoxLayout()
        self.setLayout(layout)

        # Plot preview on the left
        plot_layout = QVBoxLayout()
        self.figure = Figure(figsize=(4, 3))
        self._set_background()
        self.canvas = FigureCanvas(self.figure)
        plot_layout.addWidget(self.canvas)
        layout.addLayout(plot_layout, 1)

        # Middle column with band check boxes
        self.check_group = QGroupBox("Bands")
        self.check_layout = QVBoxLayout()
        self.check_group.setLayout(self.check_layout)
        layout.addWidget(self.check_group)

        # Right column with log scale toggle and pop out button
        ctrl_layout = QVBoxLayout()
        self.log_check = QCheckBox("Log Scale")
        self.log_check.stateChanged.connect(self._trigger_update)
        ctrl_layout.addWidget(self.log_check)

        self.pop_btn = QPushButton("Pop Out")
        self.pop_btn.clicked.connect(self.show_popup)
        ctrl_layout.addWidget(self.pop_btn)

        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)

        # Default number of KDE sample points
        self.points = 200

    def _set_background(self):
        """Update figure background to match Qt palette."""
        color = self.palette().window().color().name()
        self.figure.set_facecolor(color)

    def _trigger_update(self):
        """Helper to update distributions for the current view."""
        view_idx = self.viewer.dims.current_step[0]
        self.update_histograms(view_idx)

    def _get_gray_layers(self):
        group = self.layer_manager.groups.get(LayerType.GRAY_BAND.value)
        if not group:
            return []
        return [layer for layer, _ in group.get("layers", [])]

    def update_histograms(self, view_idx):
        """Compute and display distributions for all gray-band layers."""
        self.figure.clear()
        self._set_background()
        ax = self.figure.add_subplot(111)

        layers = self._get_gray_layers()
        points = self.points
        use_log = self.log_check.isChecked()

        # Ensure checkboxes exist for each layer
        for layer in layers:
            if layer not in self.layer_checks:
                check = QCheckBox(layer.name)
                check.setChecked(True)
                check.stateChanged.connect(self._trigger_update)
                self.layer_checks[layer] = check
                self.check_layout.addWidget(check)

        x_min, x_max = None, None
        for layer in layers:
            if not self.layer_checks.get(layer, None) or not self.layer_checks[layer].isChecked():
                continue
            data = layer.data[view_idx]
            data = data[np.isfinite(data)]
            if data.size == 0:
                continue
            kde = gaussian_kde(data.ravel())
            x = np.linspace(data.min(), data.max(), points)
            y = kde(x)
            ax.plot(x, y, label=layer.name)
            x_min = x.min() if x_min is None else min(x_min, x.min())
            x_max = x.max() if x_max is None else max(x_max, x.max())

        if layers:
            ax.legend(fontsize="small")
        ax.set_xlabel("Value")
        ax.set_ylabel("Density")
        if x_min is not None and x_max is not None:
            ax.set_xlim(x_min, x_max)
        if use_log:
            ax.set_yscale("log")
        else:
            ax.set_yscale("linear")

        self.canvas.draw_idle()
        if self.popup is not None and self.popup.isVisible():
            self._redraw_popup()

    def show_popup(self):
        """Open the current plot in a separate window."""
        if self.popup is None:
            self.popup = QDialog(self)
            self.popup.setWindowTitle("Histograms")
            layout = QVBoxLayout()
            self.popup.setLayout(layout)
            fig = Figure(figsize=(5, 4))
            fig.set_facecolor(self.palette().window().color().name())
            canvas = FigureCanvas(fig)
            layout.addWidget(canvas)
            self.popup_canvas = canvas
            self.popup_fig = fig
        self.popup.show()
        self._redraw_popup()

    def _redraw_popup(self):
        """Redraw the popout figure with current data."""
        if not hasattr(self, "popup_fig"):
            return
        fig = self.popup_fig
        fig.clear()
        ax = fig.add_subplot(111)
        layers = self._get_gray_layers()
        points = self.points
        use_log = self.log_check.isChecked()
        for layer in layers:
            if not self.layer_checks.get(layer, None) or not self.layer_checks[layer].isChecked():
                continue
            data = layer.data[self.viewer.dims.current_step[0]]
            data = data[np.isfinite(data)]
            if data.size == 0:
                continue
            kde = gaussian_kde(data.ravel())
            x = np.linspace(data.min(), data.max(), points)
            y = kde(x)
            ax.plot(x, y, label=layer.name)
        if layers:
            ax.legend(fontsize="small")
        ax.set_xlabel("Value")
        ax.set_ylabel("Density")
        if use_log:
            ax.set_yscale("log")
        else:
            ax.set_yscale("linear")
        self.popup_canvas.draw_idle()

