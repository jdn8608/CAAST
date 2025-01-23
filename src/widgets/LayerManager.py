"""
Module to manage layers for the napari viewer.

This can organize layers into category groups to allow users to quickly select types of layers at a time.
This replaces the default dockLayerList form napari
"""

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QMenu,
    QAction,
    QWidget,
)
from PyQt5.QtCore import Qt, pyqtSignal


class LayerManager(QWidget):
    """Widget to replace Napari's default layer list with a group-organized layer manager"""

    # PyQt signal for other widgets when layer name changes
    layer_renamed = pyqtSignal(str, str)

    def __init__(self, napari_viewer, init_groups=None):
        super().__init__()
        self.viewer = napari_viewer
        self.groups = {}  # Dictionary to store groups and their layers

        # Main layout for the widget
        main_layout = QVBoxLayout()
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Layer Groups")
        self.tree_widget.setEditTriggers(
            QTreeWidget.NoEditTriggers)  # Disable editing by default
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setDragDropMode(QTreeWidget.InternalMove)
        main_layout.addWidget(self.tree_widget)

        # Buttons for controlling viewer settings
        button_layout = QHBoxLayout()

        # Toggle Grid Mode Button
        self.grid_button = QPushButton("Toggle Grid View")
        self.grid_button.clicked.connect(self.toggle_grid_mode)
        button_layout.addWidget(self.grid_button)

        # Reset View Button
        self.reset_view_button = QPushButton("Reset View")
        self.reset_view_button.clicked.connect(self.reset_view)
        button_layout.addWidget(self.reset_view_button)

        main_layout.addLayout(button_layout)

        # Set the main layout
        self.setLayout(main_layout)

        # Connect tree widget events
        self.tree_widget.itemChanged.connect(self.on_item_changed)
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(
            self.show_context_menu)

        self.tree_widget.dropEvent = self.on_drop_event  # Override drop event
        self.tree_widget.setDefaultDropAction(Qt.MoveAction)
        self.tree_widget.viewport().setAcceptDrops(True)
        #help(self.tree_widget)

        # Add initial groups
        if init_groups is not None:
            if isinstance(init_groups, list):
                for g in init_groups:
                    self.add_group(group_name=g)
            elif isinstance(init_groups, str):
                self.add_groups(group_name=init_groups)

    def add_group(self, group_name):
        """Add a new group to the tree."""
        if group_name not in self.groups:
            group_item = QTreeWidgetItem([group_name])
            group_item.setFlags(group_item.flags() | Qt.ItemIsUserCheckable)
            group_item.setCheckState(0, Qt.Checked)  # Checked by default
            group_item.setFlags(group_item.flags()
                                & ~Qt.ItemIsEditable)  # Disable editing
            self.tree_widget.addTopLevelItem(group_item)
            self.groups[group_name] = {"item": group_item, "layers": []}

    def add_layer_to_group(self, group_name, layer, target_layer_name=None):
        """Add a layer to a group. If target_layer_name is None, append
            the new item... else, insert after where this item is found"""
        if group_name not in self.groups:
            # Add group_name to the groups if not found...
            self.add_group(group_name)
        group_item = self.groups[group_name]["item"]
        layer_item = QTreeWidgetItem([layer.name])
        layer_item.setFlags(
            layer_item.flags()
            | Qt.ItemIsUserCheckable)  # Enable context menu for layers
        layer_item.setCheckState(0, Qt.Checked)  # Checked by default

        # If there is a target layer for the drag event... insert the dragged
        # layer where the target is
        if target_layer_name is not None:
            insert_pos = None
            # Search for the target name
            for index, group_child in enumerate(
                    self.groups[group_name]["layers"]):
                if group_child[0].name == target_layer_name:
                    insert_pos = index
                    break  # target found, exit for

            # If the target was found, insert it
            if insert_pos is not None:
                group_item.insertChild(insert_pos, layer_item)
                self.groups[group_name]["layers"].insert(
                    insert_pos, (layer, layer_item))
                return

        # If there is no target layer or if it is not found.. append the layer
        group_item.addChild(layer_item)
        self.groups[group_name]["layers"].append((layer, layer_item))

    def on_item_clicked(self, item, column):
        """Handle layer selection."""
        if item.parent():  # Only handle clicks on layers
            layer_name = item.text(0)
            for layer in self.viewer.layers:
                if layer.name == layer_name:
                    self.viewer.layers.selection = [layer]  # Select the layer

    def toggle_grid_mode(self):
        """Toggle grid mode in the viewer."""
        self.viewer.grid.enabled = not self.viewer.grid.enabled

    def reset_view(self):
        """Reset the view to the original state."""
        self.viewer.reset_view()

    def show_context_menu(self, position):
        item = self.tree_widget.itemAt(position)
        if item and item.parent():  # Only show context menu for layers
            menu = QMenu()
            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self.rename_layer(item))
            menu.addAction(rename_action)
            menu.exec_(self.tree_widget.viewport().mapToGlobal(position))

    def rename_layer(self, item):
        # Temporarily enable editing and ensure item is editable
        previous_triggers = self.tree_widget.editTriggers()
        self.tree_widget.setEditTriggers(QTreeWidget.AllEditTriggers)
        item.setFlags(item.flags()
                      | Qt.ItemIsEditable)  # Ensure item is editable
        self.tree_widget.editItem(item)
        item.setFlags(
            item.flags()
            & ~Qt.ItemIsEditable)  # Revert to non-editable after editing
        self.tree_widget.setEditTriggers(previous_triggers)

    def on_drop_event(self, event):
        """Handle drag-and-drop functionality to move layers between groups."""
        dragged_item = self.tree_widget.currentItem()
        target_item = self.tree_widget.itemAt(event.pos())

        if not dragged_item or not dragged_item.parent():
            event.ignore()
            return  # Prevent dropping outside of groups or onto other layers

        if target_item:
            if target_item.parent() is None:  # Only allow dropping into groups
                group_name = target_item.text(0)
                target_layer_name = None
            else:
                group_name = target_item.parent().text(0)
                target_layer_name = target_item.text(0)

            source_group_name = dragged_item.parent().text(0)
            layer_name = dragged_item.text(0)

            print(
                f"Moving {layer_name} from {source_group_name} to {group_name}"
            )

            # Remove the layer from the old group
            old_group = self.groups[source_group_name]
            old_group["layers"] = [
                l for l in old_group["layers"] if l[1] != dragged_item
            ]

            # Add the layer to the new group
            for layer in self.viewer.layers:
                if layer.name == layer_name:
                    print(f"Adding {layer.name} to {group_name}")
                    self.add_layer_to_group(
                        group_name, layer, target_layer_name=target_layer_name)
                    break

            # accept event changes
            event.accept()
        else:
            event.ignore()

    def on_item_changed(self, item):
        """Handle visibility toggle for groups and layers, and renaming of layers."""
        if item.parent() is None:  # Group visibility toggle
            group_name = item.text(0)
            visible = item.checkState(0) == Qt.Checked
            for layer, layer_item in self.groups[group_name]["layers"]:
                if layer_item:
                    layer.visible = visible
                    layer_item.setCheckState(
                        0, Qt.Checked if visible else Qt.Unchecked)
        else:  # Layer visibility toggle or rename
            layer_name = item.text(0)
            parent_item = item.parent()
            group_name = parent_item.text(0)

            for layer, layer_item in self.groups[group_name]["layers"]:
                if layer_item == item:
                    # Update visibility
                    layer.visible = item.checkState(0) == Qt.Checked

                    # Update layer name if it was renamed
                    if layer.name != layer_name:
                        old_name = layer.name
                        layer.name = layer_name
                        # Emit signal for layer renaming
                        self.layer_renamed.emit(old_name, layer_name)
