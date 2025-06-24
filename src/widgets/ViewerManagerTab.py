from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTextEdit, QGroupBox, QSizePolicy
)


class ViewerManagerTab(QWidget):
    """Widget to manage extra viewers."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Column 1: Viewer layer indicator
        info_group = QGroupBox("Viewer Layers")
        info_group.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        info_group.setFixedWidth(400)
        info_layout = QVBoxLayout()
        self.layer_info = QTextEdit()
        self.layer_info.setReadOnly(True)
        self.layer_info.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        info_layout.addWidget(self.layer_info)
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # Column 2: Add layer to viewer
        add_group = QGroupBox("Add Layer")
        add_group.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        add_group.setFixedWidth(300)
        add_layout = QVBoxLayout()
        self.layer_selector = QComboBox()
        self.viewer_selector_add = QComboBox()
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self.add_layer)
        add_layout.addWidget(self.layer_selector)
        add_layout.addWidget(self.viewer_selector_add)
        add_layout.addWidget(self.add_btn)
        add_group.setLayout(add_layout)
        main_layout.addWidget(add_group)

        # Column 3: Close viewer controls
        close_group = QGroupBox("Close Viewer")
        close_group.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        close_group.setFixedWidth(200)
        close_layout = QVBoxLayout()
        self.viewer_selector = QComboBox()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close_viewer)
        close_layout.addWidget(self.viewer_selector)
        close_layout.addWidget(self.close_btn)
        close_group.setLayout(close_layout)
        main_layout.addWidget(close_group)

        # Column 4: Swap viewer controls
        swap_group = QGroupBox("Swap Viewers")
        swap_group.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        swap_group.setFixedWidth(400)
        swap_layout = QVBoxLayout()
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Swap"))
        self.swap_a = QComboBox()
        row1.addWidget(self.swap_a)
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("with"))
        self.swap_b = QComboBox()
        row2.addWidget(self.swap_b)
        self.swap_btn = QPushButton("Swap")
        self.swap_btn.clicked.connect(self.swap_viewers)
        swap_layout.addLayout(row1)
        swap_layout.addLayout(row2)
        swap_layout.addWidget(self.swap_btn)
        swap_group.setLayout(swap_layout)
        main_layout.addWidget(swap_group)

        main_layout.addStretch()

        self.update_controls()

    def update_controls(self):
        """Refresh dropdowns and layer indicators."""
        self.update_viewer_dropdowns()
        self.update_layer_dropdown()
        self.update_layer_info()

    def update_viewer_dropdowns(self):
        viewer_names = [f"Viewer {i+1}" for i in range(1, len(self.parent.viewers))]
        for combo in [self.viewer_selector, self.swap_a, self.swap_b, self.viewer_selector_add]:
            combo.clear()
            combo.addItems(viewer_names)
        # option for new viewer when adding layers
        self.viewer_selector_add.addItem("+ New Viewer")

    def update_layer_dropdown(self):
        self.layer_selector.clear()
        for layer in self.parent.main_viewer.layers:
            if layer.name != "Cursor":
                self.layer_selector.addItem(layer.name)

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
        idx = self.viewer_selector.currentIndex()
        if idx == -1:
            return
        idx += 1
        if 1 <= idx < len(self.parent.viewers):
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

    def add_layer(self):
        layer_name = self.layer_selector.currentText()
        idx = self.viewer_selector_add.currentIndex()
        if layer_name == "":
            return
        if idx == -1:
            return
        if idx == self.viewer_selector_add.count() - 1:
            viewer_idx = None
        else:
            viewer_idx = idx + 1
        self.parent.display_layer_in_viewer(layer_name, viewer_idx)
        self.update_controls()
