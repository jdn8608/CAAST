from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTextEdit, QGroupBox
)
from qtpy.QtCore import Qt


class ViewerManagerTab(QWidget):
    """Widget to manage extra viewers."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Left: Viewer layer indicator
        info_group = QGroupBox("Viewer Layers")
        info_layout = QVBoxLayout()
        self.layer_info = QTextEdit()
        self.layer_info.setReadOnly(True)
        info_layout.addWidget(self.layer_info)
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # Right: Close and swap controls stacked vertically
        controls_layout = QVBoxLayout()

        close_group = QGroupBox("Close Viewer")
        close_layout = QHBoxLayout()
        self.viewer_selector = QComboBox()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close_viewer)
        close_layout.addWidget(QLabel("Select"))
        close_layout.addWidget(self.viewer_selector)
        close_layout.addWidget(self.close_btn)
        close_group.setLayout(close_layout)
        controls_layout.addWidget(close_group)

        swap_group = QGroupBox("Swap Viewers")
        swap_layout = QHBoxLayout()
        self.swap_a = QComboBox()
        self.swap_b = QComboBox()
        self.swap_btn = QPushButton("Swap")
        self.swap_btn.clicked.connect(self.swap_viewers)
        swap_layout.addWidget(self.swap_a)
        swap_layout.addWidget(QLabel("↔"))
        swap_layout.addWidget(self.swap_b)
        swap_layout.addWidget(self.swap_btn)
        swap_group.setLayout(swap_layout)
        controls_layout.addWidget(swap_group)

        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)

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
