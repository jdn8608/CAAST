from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox, QPushButton, QWidget, QLabel
from widgets.read_write_outputs import save_labels

def create_buttons(viewer, labels_layer, output_filepath, dataset_name=None, 
			qual_labels=None, area="top"):


	# Create a save button widget
	save_button_widget = QWidget()
	save_button_layout = QVBoxLayout()

	save_button_text = 'Save Labels'


	if qual_labels:
		qual_dict, grid_layout = create_qual_dropdowns(qual_labels)
		save_button_layout.addLayout(grid_layout)
		save_button_text += ' & Flags'
	else:
		qual_dict={}
	
	# Create the Save & Submit Button
	save_button = QPushButton(save_button_text)
	save_button.clicked.connect(lambda: save_labels(labels_layer.data, qual_dict, output_filepath, dataset_name))
	save_button_layout.addWidget(save_button)
	save_button_widget.setLayout(save_button_layout)

        # Add the button widget to Napari's dock
	viewer.window.add_dock_widget(save_button_widget, area=area)

def create_qual_dropdowns(qual_labels):
	qual_dict = dict((q,QComboBox()) for q in qual_labels)

	grid_layout = QGridLayout()
	grid_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins around the grid layout
	grid_layout.setSpacing(10)

	# Add label and dropdown for each qualitative label in the grid layout
	max_columns = 4
	row = 0
	col = 0

	# Add label and dropdown for each qualitative label
	for label_text, combo_box in qual_dict.items():
		combo_box.addItems(["Unclear", "Yes", "No"])
		combo_box.setCurrentText("Unclear")  # Set "Unclear" as default
		combo_box.setFixedWidth(200)

		label_widget = QLabel(label_text.replace("_", " ").capitalize())
		grid_layout.addWidget(label_widget, row, col)
		grid_layout.addWidget(combo_box, row, col + 1)

		col += 2
		if col >= max_columns * 2:  # Move to the next row after 4 pairs
			col = 0
			row += 1

	return qual_dict, grid_layout
