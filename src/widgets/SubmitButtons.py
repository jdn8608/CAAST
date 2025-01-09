from qtpy.QtWidgets import QPushButton, QWidget

from util.read_write_outputs import save_labels


def create_save_button(button_text,
                       output_filepath,
                       labels_layer=None,
                       instrument_views=None,
                       dataset_name=None,
                       scene_labels_dict=None,
                       review_csv_filepath=None,
                       review_dropdown=None,
                       review_grader=None,
                       notes_textbox=None,
                       width=None):
    """Creates and returns a submit button that is conencted to certain save options based
    on pass-in parameters.
    """
    # Create the Save & Submit Button
    save_button = QPushButton(button_text)
    if width:
        save_button.setFixedWidth(width)
    # Connect the button's click event to a call to save_labels()
    save_button.clicked.connect(
        lambda: save_labels(output_filepath=output_filepath,
                            labels=labels_layer,
                            dataset_name=dataset_name,
                            views=instrument_views,
                            scene_labels_dict=scene_labels_dict,
                            review_filepath=review_csv_filepath,
                            review_dropdown=review_dropdown,
                            review_grader=review_grader,
                            notes_textbox=notes_textbox))
    return save_button
