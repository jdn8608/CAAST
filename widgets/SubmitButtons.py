from PyQt5.QtGui import QPainter, QFontMetrics
from PyQt5.QtWidgets import QSlider, QStyleOptionSlider, QStyle
from PyQt5.QtCore import Qt, QPoint
from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox, QPushButton, QWidget, QLabel
from widgets.read_write_outputs import save_labels


def create_save_button(button_text,
                       output_filepath,
                       labels_layer=None,
                       instrument_views=None,
                       dataset_name=None,
                       scene_labels_dict=None,
                       review_csv_filepath=None,
                       review_dropdown=None,
                       review_grader=None,
                       width=None):
    # Create the Save & Submit Button
    save_button = QPushButton(button_text)
    if width:
        save_button.setFixedWidth(width)
    save_button.clicked.connect(
        lambda: save_labels(output_filepath=output_filepath,
                            labels=labels_layer,
                            dataset_name=dataset_name,
                            views=instrument_views,
                            scene_labels_dict=scene_labels_dict,
                            review_filepath=review_csv_filepath,
                            review_dropdown=review_dropdown,
                            review_grader=review_grader))
    return save_button


def create_scene_dropdowns(scene_labels, priors=None):
    scene_labels_dict = dict((q, QComboBox()) for q in scene_labels)

    grid_layout = QGridLayout()
    grid_layout.setContentsMargins(0, 0, 0,
                                   0)  # Remove margins around the grid layout
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


class GradeSlider(QWidget):

    def __init__(self, min_val, max_val, interval=1, init_val=1):
        super().__init__()
        layout = QVBoxLayout()

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setSingleStep(interval)
        self.slider.setTickPosition(
            QSlider.TicksBelow)  # Adds default ticks too
        self.slider.setMinimumWidth(300)
        layout.addWidget(self.slider)

        self.slider.valueChanged.connect(self.on_value_changed)
        self.value = init_val
        self.slider.setValue(self.value)

        self.setLayout(layout)

    def on_value_changed(self):
        self.value = self.slider.value()

    def paintEvent(self, event):
        super().paintEvent(event)

        # Manually draw tick marks
        painter = QPainter(self)
        slider_style = self.slider.style()
        style_option = QStyleOptionSlider()
        style_option.initFrom(self.slider)
        style_option.orientation = self.slider.orientation()

        # Retrieve slider geometry details
        handle_length = slider_style.pixelMetric(QStyle.PM_SliderLength,
                                                 style_option, self.slider)
        available_width = slider_style.pixelMetric(
            QStyle.PM_SliderSpaceAvailable, style_option, self.slider)

        slider_x = self.slider.x()
        slider_y = self.slider.y() + self.slider.height()

        num_ticks = self.slider.maximum() - self.slider.minimum() + 1
        tick_spacing = available_width / (num_ticks - 1)

        for i in range(num_ticks):
            # Calculate the exact position of each tick
            x = int(slider_x + handle_length / 2 + i * tick_spacing)
            y = slider_y

            # Draw the tick mark
            painter.drawLine(QPoint(x, y), QPoint(x, y + 10))  # Tick mark

            # Draw the label above the tick mark
            label = str(self.slider.minimum() + i)
            font_metrics = QFontMetrics(painter.font())
            label_width = font_metrics.horizontalAdvance(label)
            label_x = x - label_width // 2
            label_y = y - 20  # Position the label above the tick mark
            painter.drawText(QPoint(label_x, label_y), label)
