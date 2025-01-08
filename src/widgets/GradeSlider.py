"""
This module creates a grade slider widget.

This widget is used to "Grade" scenes' cloud mask labels on an integer scale (not-continous).
"""
from PyQt5.QtGui import QPainter, QFontMetrics
from PyQt5.QtWidgets import QSlider, QStyleOptionSlider, QStyle, QHBoxLayout, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QPoint
#from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget


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
