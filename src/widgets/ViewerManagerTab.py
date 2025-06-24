from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTextEdit
)
from qtpy.QtCore import Qt


class ViewerManagerTab(QWidget):
    """Widget to manage extra viewers."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Close viewer controls
        close_layout = QHBoxLayout()
        close_layout.addWidget(QLabel("Select Viewer:"))
        self.viewer_selector = QComboBox()
        close_layout.addWidget(self.viewer_selector)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close_viewer)
        close_layout.addWidget(self.close_btn)
        layout.addLayout(close_layout)

        # Layer info
        self.layer_info = QTextEdit()
        self.layer_info.setReadOnly(True)
        layout.addWidget(self.layer_info)

        # Swap controls
        swap_layout = QHBoxLayout()
        swap_layout.addWidget(QLabel("Swap Viewer"))
        self.swap_a = QComboBox()
        self.swap_b = QComboBox()
        swap_layout.addWidget(self.swap_a)
        swap_layout.addWidget(QLabel("with"))
        swap_layout.addWidget(self.swap_b)
        self.swap_btn = QPushButton("Swap")
        self.swap_btn.clicked.connect(self.swap_viewers)
        swap_layout.addWidget(self.swap_btn)
        layout.addLayout(swap_layout)

        self.update_controls()

    def update_controls(self):
        viewer_names = [f"Viewer {i+1}" for i in range(1, len(self.parent.viewers))]
        for combo in [self.viewer_selector, self.swap_a, self.swap_b]:
            combo.clear()
            combo.addItems(viewer_names)
        self.update_layer_info()

    def update_layer_info(self):
        info_lines = []
        for idx, viewer in enumerate(self.parent.viewers[1:], start=2):
            if viewer.layers:
                layer_name = viewer.layers[0].name
            else:
                layer_name = "(empty)"
            info_lines.append(f"Viewer {idx}: {layer_name}")
        self.layer_info.setPlainText("\n".join(info_lines))

    def close_viewer(self):
        idx = self.viewer_selector.currentIndex() + 1
        if idx < len(self.parent.viewers):
            viewer = self.parent.viewers[idx]
            widget = viewer.window._qt_window
            self.parent.remove_viewer(viewer, widget)
            self.update_controls()

    def swap_viewers(self):
        idx1 = self.swap_a.currentIndex() + 1
        idx2 = self.swap_b.currentIndex() + 1
        if idx1 == idx2:
            return
        self.parent.swap_viewer_contents(idx1, idx2)
        self.update_layer_info()
