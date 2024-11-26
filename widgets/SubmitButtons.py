from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox, QPushButton, QWidget, QLabel
from widgets.read_write_outputs import save_labels

def create_buttons(viewer, labels_layer, output_filepath, instrument_views, dataset_name=None, 
			scene_labels=None, area="top"):


	# Create a save button widget
	save_button_widget = QWidget()
	save_button_layout = QVBoxLayout()

	save_button_text = 'Save Labels'


	if scene_labels:
		if isinstance(scene_labels, list): 
			scene_labels_dict, grid_layout = create_scene_dropdowns(scene_labels)
		else:
			scene_labels_dict, grid_layout = create_scene_dropdowns(list(scene_labels.keys()), priors=list(scene_labels.values()))
		save_button_layout.addLayout(grid_layout)
		save_button_text += ' & Flags'
	else:
		scene_labels_dict={}
	
	# Create the Save & Submit Button
	save_button = QPushButton(save_button_text)
	save_button.clicked.connect(lambda: save_labels(labels_layer.data, output_filepath, dataset_name, instrument_views, scene_labels_dict,))
	save_button_layout.addWidget(save_button)
	save_button_widget.setLayout(save_button_layout)

        # Add the button widget to Napari's dock
	viewer.window.add_dock_widget(save_button_widget, area=area)

def create_scene_dropdowns(scene_labels, priors=None):
	scene_labels_dict = dict((q,QComboBox()) for q in scene_labels)

	grid_layout = QGridLayout()
	grid_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins around the grid layout
	grid_layout.setSpacing(10)

	# Add label and dropdown for each scene-level labels in the grid layout
	max_columns = 4
	row = 0
	col = 0

	# Add label and dropdown for each scene-level label
	for i, (label_text, combo_box) in enumerate(scene_labels_dict.items()):
		combo_box.addItems(["Unclear", "Yes", "No"])
		if priors:
			combo_box.setCurrentText(priors[i])  # Set "Unclear" as default
		else:
			combo_box.setCurrentText("Unclear")  # Set "Unclear" as default
		combo_box.setFixedWidth(200)

		label_widget = QLabel(label_text.replace("_", " ").capitalize())
		grid_layout.addWidget(label_widget, row, col)
		grid_layout.addWidget(combo_box, row, col + 1)

		col += 2
		if col >= max_columns * 2:  # Move to the next row after 4 pairs
			col = 0
			row += 1

	return scene_labels_dict, grid_layout
