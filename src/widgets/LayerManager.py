"""
Module to manage layers for the napari viewer.

This can organize layers into category groups to allow users to quickly select types of layers at a time.
This replaces the default dockLayerList form napari
"""

import numpy as np

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
from util.LayerType import LayerType


class LayerManager(QWidget):
    """Widget to replace Napari's default layer list with a group-organized layer manager"""

    # PyQt signal for other widgets when layer name changes
    layer_renamed = pyqtSignal(str, str)

    def __init__(self, napari_viewer, shape, init_groups=None):
        super().__init__(None)
        self.viewer = napari_viewer
        self.image_shape = shape
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
        button_layout = QVBoxLayout()
        button_top_layout = QHBoxLayout()
        button_mid_layout = QHBoxLayout()
        button_bot_layout = QHBoxLayout()

        # Toggle All Groups
        self.togg_button = QPushButton("Toggle All Groups")
        self.togg_button.clicked.connect(self.toggle_all_groups)
        button_top_layout.addWidget(self.togg_button)

        # Add a new layer
        self.new_labels_button = QPushButton("New Labels Layer")
        self.new_labels_count = 1
        self.new_labels_button.clicked.connect(self.add_blank_labels)
        button_top_layout.addWidget(self.new_labels_button)

        # Split View
        self.split_view_button = QPushButton("Toggle Split View")
        button_mid_layout.addWidget(self.split_view_button)

        # Re-order Layers
        self.reorder_layers_button = QPushButton("Re-Order Visual")
        self.reorder_layers_button.clicked.connect(self.toggle_layer_list)
        button_mid_layout.addWidget(self.reorder_layers_button)

        # Toggle Grid Mode Button
        self.grid_button = QPushButton("Toggle Grid View")
        self.grid_button.clicked.connect(self.toggle_grid_mode)
        button_bot_layout.addWidget(self.grid_button)

        # Reset View Button
        self.reset_view_button = QPushButton("Reset View")
        self.reset_view_button.clicked.connect(self.reset_view)
        button_bot_layout.addWidget(self.reset_view_button)

        button_layout.addLayout(button_top_layout)
        button_layout.addLayout(button_mid_layout)
        button_layout.addLayout(button_bot_layout)
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

    def toggle_layer_list(self):
        dock = self.viewer.window.qt_viewer.dockLayerList
        dock.setFloating(True)
        dock.setVisible(True)

    def add_blank_labels(self):
        """Add a new blank labels layer to the viewer and MANUAL LABELS group."""
        im_temp = self.viewer.add_labels(
            np.zeros(self.image_shape, dtype=int),
            name=f"New Labels {self.new_labels_count}")
        self.new_labels_count += 1
        self.add_layer_to_group(LayerType.MANUAL_LABELS.value, im_temp)
        return

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

    def dragMoveEvent(self, event):
        """Override dragMoveEvent to suppress built-in Qt animations."""
        event.accept()  # Prevents Qt from thinking the drop is invalid

    def on_drop_event(self, event):
        """Handle drag-and-drop functionality to move layers between groups."""
        dragged_item = self.tree_widget.currentItem()
        target_item = self.tree_widget.itemAt(event.pos())

        # Prevent dropping outside of groups or onto other layers
        if not dragged_item:
            event.ignore()
            return
        # Group re-ordering: drag groups only to positions of other groups
        elif dragged_item.parent() is None:
            if target_item and target_item.parent() is None:
                # Get indexes of dragged and target items for shifting
                dragged_index = self.tree_widget.indexOfTopLevelItem(
                    dragged_item)
                target_index = self.tree_widget.indexOfTopLevelItem(
                    target_item)

                # Ensure indexs of swap are in-bounds
                if dragged_index != -1 and target_index != -1:
                    # Reorder the top-level items
                    self.tree_widget.takeTopLevelItem(dragged_index)
                    self.tree_widget.insertTopLevelItem(
                        target_index, dragged_item)

                    # Update the group order in the internal dictionary
                    dragged_group_name = dragged_item.text(0)
                    #reordered_groups = [self.tree_widget.topLevelItem(i).text(0) for i in range(self.tree_widget.topLevelItemCount())]
                    #self.groups = {key: self.groups[key] for key in reordered_groups if key in self.groups}

                    reordered_groups = list(self.groups.keys())
                    removed = reordered_groups.pop(dragged_index)
                    reordered_groups.insert(target_index, removed)
                    new_order = {
                        key: self.groups[key]
                        for key in reordered_groups
                    }

                    self.groups = new_order

                    #event.acceptProposedAction()
                    # Current bug: If event is accepted, a top child is deleted
                    # if the event is ignore, proper drag drop handling is allowed
                    # but then a snap back animation is played... needs further
                    # investigation in the future for correction. Current implementation
                    # works and only has a visual bug.
                    event.ignore()

                else:  # indexes out of bounds... ignore event
                    event.ignore()
            else:  # either target does not exist or is not a group... ignore event
                event.ignore()

        # Layer dragging to or within groups
        elif target_item:
            # Dragging to a group directly
            if target_item.parent() is None:  # Only allow dropping into groups
                group_name = target_item.text(0)
                target_layer_name = None
            # Dragging to another layer (re-order or adding to a new group) in-place
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

    def print_top_level_items(self):
        print('----------------------------------')
        print("Current Groups in QTreeWidget:")
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            print(f"{i}: {item.text(0)}")

    def print_groups(self):
        print("--Current Groups--")
        for i, k in enumerate(self.groups.keys()):
            print(f"{i}: {k}")

    def toggle_all_groups(self):
        """Toggle visibility of all groups."""
        all_checked = all(group["item"].checkState(0) == Qt.Checked
                          for group in self.groups.values())

        # Determine new state: If all are checked, uncheck all. Otherwise, check all.
        new_state = Qt.Unchecked if all_checked else Qt.Checked

        for group in self.groups.values():
            group_item = group["item"]
            group_item.setCheckState(0, new_state)  # Toggle group checkbox
            # Layer toggles will be auto caught by on_item_changed() with event handling
