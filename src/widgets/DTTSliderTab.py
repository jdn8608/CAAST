from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSlider,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QFrame,
)
from qtpy.QtCore import Qt

import numpy as np


# Author(s) Guangyu Zhao and Michie De Vera
# From the JPL MCM V5 code
def get_cm_confidence(DTT, activation, N, fill_val_2, fill_val_3):
    """calculates final cloud mask based of the DTT, the activation value, and
       N tests needed to activate.

    [Section N/A]

    Arguments:
        DTT {3D narray} -- first 2 axies are granule dimesions, 3rd axies contains
                           DTT for each observable in this order:
                           WI, NDVI, NDSI, VIS Ref, NIR Ref, SVI, Cirrus
        activation {1D narray} -- values for each observable's DTT to exceed to
                                  be called cloudy
        N {integer} -- number of observables which have to activate to be called
                       cloudy.
        fill_val_1 {integer} -- defined in congifg file; not applied due to surface type
        fill_val_2 {integer} -- defined in congifg file; low quality radiance
        fill_val_3 {integer} -- defined in congifg file; no data

    Returns:
        2D narray -- cloud mask; cloudy (0) clear(1) bad data (2) no data (3)

    """
    #create the mask only considering the activation & fill values, not N yet
    #this creates a stack of cloud masks, 7 observables deep, with fill values
    #untouched

    #cloudy_idx contains indicies where each observable independently returned
    #cloudy. The array it refers to is (X,Y,7) for 7 observables calculated over
    #the swath of MAIA
    #essentailly the format is of numpy.where() for 3D array to use later
    # [[    0.     0.     0. ...,  1265.  1265.  1267.]
    #  [   39.    42.    43. ...,   318.   319.   317.]
    #  [    0.     0.     0. ...,     6.     6.     6.]]

    #we must do it like this since each observable has a unique activation value

    #execute above comment blocks
    num_tests = activation.size
    cloudy_idx = np.where(DTT[:, :, 0] >= activation[0])
    #stack the 2D cloudy_idx with a 1D array of zeros denoting 0th element along
    #3rd axis
    zeroth_axis = np.zeros((np.shape(cloudy_idx)[1]))
    cloudy_idx = np.vstack((cloudy_idx, zeroth_axis))

    #do the same as above in the loop but with the rest of the observables
    #which are stored along the 3rd axis
    for test_num in range(1, num_tests):
        new_cloudy_idx = np.where(DTT[:, :, test_num] >= activation[test_num])
        nth_axis = np.ones((np.shape(new_cloudy_idx)[1])) * test_num
        new_cloudy_idx = np.vstack((new_cloudy_idx, nth_axis))
        cloudy_idx = np.concatenate((cloudy_idx, new_cloudy_idx), axis=1)

    cloudy_idx = cloudy_idx.astype(int)  #so we can index with this result

    #find indicies where fill values are
    failed_retrieval_idx = np.where(DTT == fill_val_2)
    no_data_idx = np.where(DTT == fill_val_3)

    DTT_ = np.copy(DTT)
    DTT_[cloudy_idx[0], cloudy_idx[1], cloudy_idx[2]] = 0
    DTT_[failed_retrieval_idx] = 2
    DTT_[no_data_idx] = 3
    #can't assign value to 'maybe_cloudy' yet since it would override 'cloudy'
    #we must check the N condition before proceeding on this

    #check N condition to distinguish 'maybe_cloudy' from 'cloudy'
    #count howmany tests returned DTT >= activation value for each pixel
    #To do this, simply add along the third axis each return type for the final
    #cloud mask, 0-3 inclusive
    #check if all tests failed with DTT = -126 <- bad quality data
    #check if all tests failed with DTT = -127 <- no data
    shape = DTT[:, :, 0].shape
    cloudy_test_count = np.zeros(shape)
    failed_retrieval_count = np.zeros(shape)
    no_data_count = np.zeros(shape)

    for i in range(num_tests):
        cloudy_idx = np.where(DTT_[:, :, i] == 0)
        cloudy_test_count[cloudy_idx] += 1
        failed_retrieval_idx = np.where(DTT_[:, :, i] == 2)
        failed_retrieval_count[failed_retrieval_idx] += 1

        no_data_idx = np.where(DTT_[:, :, i] == 3)
        no_data_count[no_data_idx] += 1

    #populate final cloud mask; default of one assumes 'maybe cloudy' at all pixels
    final_cm = np.ones(shape)

    cloudy_idx = np.where(cloudy_test_count >= N)
    final_cm[cloudy_idx] = 0

    failed_retrieval_idx = np.where(failed_retrieval_count == num_tests)
    final_cm[failed_retrieval_idx] = 2

    no_data_idx = np.where(no_data_count == num_tests)
    final_cm[no_data_idx] = 3

    return final_cm


ORDERED_DTT_NAMES = [
    "DTT WI",
    "DTT NDVI",
    "DTT NDSI",
    "DTT visRef",
    "DTT nirRef",
    "DTT SVI",
    "DTT Cirrus",
]


class DTTSliderTab(QWidget):
    """Tab widget with vertical sliders for each DTT layer.

    Parameters
    ----------
    viewer : napari.Viewer
        Viewer instance used to track current view.
    initial_values : dict[int, dict[str, int]], optional
        Mapping of view index to slider values by layer name.
    activation_values : np.ndarray, optional
        Activation thresholds for each observable per view.
    num_tests : np.ndarray or None, optional
        Minimum number of tests required to activate per view.
    fill_val_2 : np.ndarray or None, optional
        Fill value 2 for each view.
    fill_val_3 : np.ndarray or None, optional
        Fill value 3 for each view.
    """

    def __init__(self, viewer, initial_values=None, activation_values=None,
                 num_tests=None, fill_val_2=None, fill_val_3=None, viewers=None):
        super().__init__()
        self.viewer = viewer
        # list of viewers to update when the mask changes
        self.viewers = viewers if viewers is not None else [viewer]
        self.activation_values = activation_values
        self.num_tests = num_tests
        self.fill_val_2 = fill_val_2
        self.fill_val_3 = fill_val_3
        self.sliders = {}
        self.text_boxes = {}
        # Slider operates in tenths to mimic float precision
        self.slider_range = (-1010, 1010)
        # Storage for slider values per view
        self.view_values = {
            k: dict(v)
            for k, v in (initial_values or {}).items()
        }
        # Storage for per-view number of tests
        self.num_tests_values = {}
        self.current_view = (self.viewer.dims.current_step[0]
                             if self.viewer.dims.ndim > 0 else 0)

        main_layout = QHBoxLayout()
        sliders_layout = QHBoxLayout()
        sliders_layout.setSpacing(80)

        # Dropdown for number of tests needed
        tests_layout = QVBoxLayout()
        tests_label = QLabel("Tests Needed")
        tests_label.setAlignment(Qt.AlignCenter)
        self.num_tests_dropdown = QComboBox()
        for i in range(1, 8):
            self.num_tests_dropdown.addItem(str(i))
        self.num_tests_dropdown.currentIndexChanged.connect(self._num_tests_changed)
        tests_layout.addWidget(tests_label)
        tests_layout.addWidget(self.num_tests_dropdown)
        init_tests = None
        if self.num_tests is not None and len(self.num_tests) > self.current_view:
            init_tests = int(self.num_tests[self.current_view])
        init_tests = self.num_tests_values.get(self.current_view, init_tests)
        if init_tests is None:
            init_tests = 1
        self.num_tests_dropdown.setCurrentIndex(max(1, int(init_tests)) - 1)

        # Gather layer references
        self.layer_dict = {}
        self.dtt_mask_layer = None
        for layer in self.viewer.layers:
            if layer.name.startswith("DTT"):
                if "mask" in layer.name.lower():
                    self.dtt_mask_layer = layer
                else:
                    self.layer_dict[layer.name] = layer

        assert self.dtt_mask_layer is not None, "DTT MASK was not found in main_viewer.layers"

        # Determine display order for sliders
        ordered_names = [n for n in ORDERED_DTT_NAMES if n in self.layer_dict]

        # Populate view_values with activation thresholds if provided
        if self.activation_values is not None:
            for view_idx in range(self.activation_values.shape[1]):
                for obs_idx, name in enumerate(ordered_names):
                    val = float(self.activation_values[obs_idx, view_idx])
                    self.view_values.setdefault(view_idx, {})
                    self.view_values[view_idx].setdefault(name, val)

        if self.num_tests is not None:
            for view_idx in range(len(self.num_tests)):
                self.num_tests_values[view_idx] = int(self.num_tests[view_idx])

        # Build slider widgets
        for name in ordered_names:
            layer = self.layer_dict[name]

            layer_layout = QHBoxLayout()
            layer_layout.setSpacing(5)

            slider = QSlider(Qt.Vertical)
            slider.setRange(*self.slider_range)
            start_val = float(self.view_values.get(self.current_view, {}).get(name, 0.0))
            slider.setValue(int(round(start_val * 10)))
            slider.valueChanged.connect(self._slider_changed)

            info_layout = QVBoxLayout()
            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            text = QLineEdit(f"{start_val:.1f}")
            text.setFixedWidth(50)
            text.editingFinished.connect(self._text_changed)
            info_layout.addWidget(label)
            info_layout.addWidget(text)

            layer_layout.addWidget(slider)
            layer_layout.addLayout(info_layout)

            sliders_layout.addLayout(layer_layout)
            self.sliders[name] = slider
            self.text_boxes[name] = text
            self.view_values.setdefault(self.current_view, {})[name] = start_val

        # Layout for radio buttons and button on the right
        button_layout = QVBoxLayout()
        self.radio_group = QButtonGroup(self)
        self.save_current_radio = QRadioButton("Save current view's config")
        self.save_all_radio = QRadioButton("Save all views' config")
        self.radio_group.addButton(self.save_current_radio)
        self.radio_group.addButton(self.save_all_radio)
        self.save_current_radio.setChecked(True)
        button_layout.addWidget(self.save_current_radio)
        button_layout.addWidget(self.save_all_radio)

        btn = QPushButton("Generate Config File\nSave Cloud Mask")
        btn.setFixedWidth(200)
        btn.setFixedHeight(100)
        # Intentionally left unconnected for now
        button_layout.addWidget(btn)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setMidLineWidth(3)
        separator.setLineWidth(3)
        separator.setStyleSheet("color: #323232 ")

        main_layout.addLayout(tests_layout, stretch=1)
        main_layout.addLayout(sliders_layout, stretch=9)
        main_layout.addWidget(separator)
        main_layout.addLayout(button_layout, stretch=1)
        self.setLayout(main_layout)

        # Connect view change event to sync slider values
        self.viewer.dims.events.current_step.connect(self._view_changed)

    def _slider_changed(self, value):
        slider = self.sender()
        for name, s in self.sliders.items():
            if s is slider:
                fval = value / 10.0
                self.text_boxes[name].setText(f"{fval:.1f}")
                self.view_values.setdefault(self.current_view,
                                            {})[name] = fval
                break
        self._apply_mask()

    def _num_tests_changed(self, index):
        self.num_tests_values[self.current_view] = index + 1

    def _text_changed(self):
        text = self.sender()
        for name, t in self.text_boxes.items():
            if t is text:
                try:
                    value = float(t.text())
                except ValueError:
                    return
                value = max(self.slider_range[0] / 10,
                            min(self.slider_range[1] / 10, value))
                self.sliders[name].setValue(int(round(value * 10)))
                self.view_values.setdefault(self.current_view,
                                            {})[name] = value
                break
        # self._apply_mask will be triggered via slider change

    def print_values(self):
        """Print current slider values for debugging."""
        values = self.view_values.get(self.current_view, {})
        print("Current DTT slider values:", values)

    def _save_current_values(self):
        self.view_values.setdefault(self.current_view, {})
        for name, slider in self.sliders.items():
            self.view_values[self.current_view][name] = slider.value() / 10.0
        if hasattr(self, 'num_tests_dropdown'):
            self.num_tests_values[self.current_view] = (
                self.num_tests_dropdown.currentIndex() + 1)

    def _load_view_values(self):
        values = self.view_values.get(self.current_view, {})
        for name, slider in self.sliders.items():
            val = float(values.get(name, 0.0))
            slider.blockSignals(True)
            self.text_boxes[name].blockSignals(True)
            slider.setValue(int(round(val * 10)))
            self.text_boxes[name].setText(f"{val:.1f}")
            slider.blockSignals(False)
            self.text_boxes[name].blockSignals(False)
        if hasattr(self, 'num_tests_dropdown'):
            default = None
            if self.num_tests is not None and len(self.num_tests) > self.current_view:
                default = int(self.num_tests[self.current_view])
            val = self.num_tests_values.get(self.current_view, default)
            if val is None:
                val = 1
            self.num_tests_dropdown.setCurrentIndex(max(1, int(val)) - 1)

    def _view_changed(self, event):
        self._save_current_values()
        self.current_view = self.viewer.dims.current_step[0]
        self._load_view_values()

    def _apply_mask(self):
        """Compute and update the DTT cloud mask for the current view."""
        ordered_names = [n for n in ORDERED_DTT_NAMES if n in self.layer_dict]
        dtt_stack = []
        for name in ordered_names:
            layer = self.layer_dict[name]
            dtt_stack.append(layer.data[self.current_view])
        if not dtt_stack:
            return
        dtt_array = np.stack(dtt_stack, axis=-1)

        thresholds = np.array([
            self.view_values.get(self.current_view, {}).get(name, 0)
            for name in ordered_names
        ])

        if self.num_tests_values:
            n_tests = int(self.num_tests_values.get(
                self.current_view,
                self.num_tests[self.current_view] if self.num_tests is not None else thresholds.size
            ))
        else:
            n_tests = int(self.num_tests[self.current_view]) if self.num_tests is not None else thresholds.size
        fv2 = float(self.fill_val_2[self.current_view]) if self.fill_val_2 is not None else -126
        fv3 = float(self.fill_val_3[self.current_view]) if self.fill_val_3 is not None else -127

        cm = get_cm_confidence(dtt_array, thresholds, n_tests, fv2, fv3)

        mask_data = self.dtt_mask_layer.data.copy()
        mask_data[self.current_view] = cm
        self.dtt_mask_layer.data = mask_data

        # Update mask layer in any additional viewers
        for viewer in self.viewers:
            if viewer is self.viewer:
                continue
            if self.dtt_mask_layer.name in viewer.layers:
                viewer.layers[self.dtt_mask_layer.name].data = mask_data
