from PyQt5.QtWidgets import (
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QCheckBox,
    QDockWidget,
    QWidget,
)
from PyQt5.QtCore import Qt


class LayerManager(QWidget):
    """Widget to replace Napari's defualt layer list with a group organized layer manager"""

    def __init__(self, napari_viewer, init_groups=None):
        super().__init__()
        self.viewer = napari_viewer
        self.groups = {}  # Dictionary to store groups and their layers

        # Create a layout and tree widget to manage groups
        layout = QVBoxLayout()
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Layer Groups")
        layout.addWidget(self.tree_widget)
        self.setLayout(layout)

        # Connect tree widget events
        self.tree_widget.itemChanged.connect(self.on_item_changed)
        self.tree_widget.itemClicked.connect(self.on_item_clicked)

        # Add initial groups
        if init_groups is not None:
            if isinstance(init_groups, list):
                for g in init_groups:
                    self.add_group(group_name=g)
            elif isinstance(init_groups, str):
                self.add_groups(group_name=init_groups)

    def add_group(self, group_name):
        """Add a new group to the tree."""
        # print(f"Adding new group: '{group_name}'")
        if group_name not in self.groups:
            group_item = QTreeWidgetItem([group_name])
            group_item.setFlags(group_item.flags() | Qt.ItemIsUserCheckable)
            group_item.setCheckState(0, Qt.Checked)  # Checked by default
            self.tree_widget.addTopLevelItem(group_item)
            self.groups[group_name] = {"item": group_item, "layers": []}

    def add_layer_to_group(self, group_name, layer):
        """Add a layer to a group."""
        # print(f"Adding Layer: '{layer}' to Group: {group_name}")
        if group_name in self.groups:
            group_item = self.groups[group_name]["item"]
            layer_item = QTreeWidgetItem([layer.name])
            layer_item.setFlags(layer_item.flags() | Qt.ItemIsUserCheckable)
            layer_item.setCheckState(0, Qt.Checked)  # Checked by default
            group_item.addChild(layer_item)
            self.groups[group_name]["layers"].append((layer, layer_item))

    def on_item_changed(self, item):
        """Handle visibility toggle for groups and layers."""
        if item.parent() is None:  # Group visibility toggle
            group_name = item.text(0)
            visible = item.checkState(0) == Qt.Checked
            for layer, layer_item in self.groups[group_name]["layers"]:
                layer.visible = visible
                layer_item.setCheckState(
                    0, Qt.Checked if visible else Qt.Unchecked)
        else:  # Layer visibility toggle
            layer_name = item.text(0)
            for group in self.groups.values():
                for layer, layer_item in group["layers"]:
                    if layer.name == layer_name:
                        layer.visible = item.checkState(0) == Qt.Checked

    def on_item_clicked(self, item, column):
        """Handle layer selection."""
        if item.parent():  # Only handle clicks on layers
            layer_name = item.text(0)
            for layer in self.viewer.layers:
                if layer.name == layer_name:
                    self.viewer.layers.selection = [layer]  # Select the layer
