"""
Author: Joseph Nied (jdnied2@illinois.edu)
Date: 12-19-2024
Description:
    The main run script for the SALT visualization tool to be ran from the command line.

    This script sub-modules with settings from configuration files to read-in, format, & 
    visualize satelitte imager data. 
"""

import argparse
import json
import os
import tempfile

# Import util scripts
from util.get_data import get_data
from util.create_tool import create_tool

# Meta-data for file
__author__ = "Joseph Nied"
__credits__ = ["Joseph Nied"]
__copyright__ = "Copyright 2007"
__license__ = "GPL"
__version__ = "3.0"
__maintainer__ = "Joseph Nied"
__email__ = "jdnied2@illinois.edu"
__status__ = "Production"


def get_from_GUI():
    """Open a small Qt GUI to gather settings from the user.

    Returns
    -------
    dict
        Dictionary containing command line style arguments for ``get_data`` and
        ``create_tool``. The keys mirror the argparse options used when running
        in COMMAND mode. If the window is closed without pressing ``Run`` the
        return value will be ``None``.
    """

    # Import Qt widgets lazily so users running in command mode do not need the
    # Qt backend at import time.
    from qtpy.QtWidgets import (
        QApplication,
        QWidget,
        QMainWindow,
        QVBoxLayout,
        QHBoxLayout,
        QTabWidget,
        QPushButton,
        QLineEdit,
        QFileDialog,
        QLabel,
        QComboBox,
        QCheckBox,
        QMessageBox,
        QFormLayout,
        QScrollArea,
    )

    from util.get_data import create_instrument_dict

    class SettingsWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.result = None
            self.setWindowTitle("SALT Configuration")

            central = QWidget()
            self.setCentralWidget(central)
            main_layout = QVBoxLayout()
            central.setLayout(main_layout)

            self.tabs = QTabWidget()
            main_layout.addWidget(self.tabs)

            self.reader_widgets = {}
            self.reader_types = {}
            self.output_widgets = {}
            self.output_types = {}

            # --- Tab 1 : file selection and flags ---
            tab1 = QWidget()
            t1 = QVBoxLayout()
            tab1.setLayout(t1)

            # file selection
            file_row = QHBoxLayout()
            self.file_edit = QLineEdit()
            browse = QPushButton("Browse")
            browse.clicked.connect(self.select_files)
            file_row.addWidget(self.file_edit)
            file_row.addWidget(browse)
            t1.addWidget(QLabel("Input files"))
            t1.addLayout(file_row)

            # file reader
            t1.addWidget(QLabel("File Reader"))
            self.reader_combo = QComboBox()
            self.reader_combo.addItems(sorted(create_instrument_dict().keys()))
            t1.addWidget(self.reader_combo)

            # label/check flags
            self.label_cb = QCheckBox("Label Mode")
            self.check_manual_cb = QCheckBox("Check Manual Labels")
            t1.addWidget(self.label_cb)
            t1.addWidget(self.check_manual_cb)

            self.load_labels_edit = QLineEdit()
            t1.addWidget(QLabel("Load Labels"))
            t1.addWidget(self.load_labels_edit)

            self.tabs.addTab(tab1, "Inputs")

            # --- Tab 2 : reader configuration ---
            tab2 = QWidget()
            t2 = QVBoxLayout()
            tab2.setLayout(t2)

            scroll2 = QScrollArea()
            scroll2.setWidgetResizable(True)
            widget2 = QWidget()
            self.reader_form = QFormLayout()
            widget2.setLayout(self.reader_form)
            scroll2.setWidget(widget2)
            t2.addWidget(scroll2)
            load_reader_btn = QPushButton("Load Config")
            load_reader_btn.clicked.connect(self.load_reader_config)
            t2.addWidget(load_reader_btn)

            self.tabs.addTab(tab2, "Reader Config")

            self.load_reader_config(default=True)

            # --- Tab 3 : output configuration ---
            tab3 = QWidget()
            t3 = QVBoxLayout()
            tab3.setLayout(t3)

            scroll3 = QScrollArea()
            scroll3.setWidgetResizable(True)
            widget3 = QWidget()
            self.output_form = QFormLayout()
            widget3.setLayout(self.output_form)
            scroll3.setWidget(widget3)
            t3.addWidget(scroll3)
            load_output_btn = QPushButton("Load Config")
            load_output_btn.clicked.connect(self.load_output_config)
            t3.addWidget(load_output_btn)

            self.tabs.addTab(tab3, "Output Config")

            self.load_output_config(default=True)

            # Run button at bottom
            run_btn = QPushButton("Run")
            run_btn.clicked.connect(self.run_clicked)
            main_layout.addWidget(run_btn)

        # --- Helper slots ---
        def select_files(self):
            files, _ = QFileDialog.getOpenFileNames(self, "Select files")
            if files:
                self.file_edit.setText(";".join(files))

        def _populate_form(self, form, widgets, types, cfg, skip_keys=()):
            while form.rowCount():
                form.removeRow(0)
            widgets.clear()
            types.clear()
            for key, val in cfg.items():
                if key in skip_keys:
                    continue
                if isinstance(val, list):
                    w = QLineEdit(", ".join(str(v) for v in val))
                    val_type = list
                elif isinstance(val, (int, bool)) and val in (0, 1, True, False):
                    w = QCheckBox()
                    w.setChecked(bool(val))
                    val_type = bool
                else:
                    w = QLineEdit(str(val))
                    val_type = type(val)
                form.addRow(QLabel(key), w)
                widgets[key] = w
                types[key] = val_type

        def load_reader_config(self, default=False):
            if default:
                fp = os.path.join(os.path.dirname(__file__),
                                  'settings', 'MAIA_proxy.json')
            else:
                fp, _ = QFileDialog.getOpenFileName(
                    self, 'Open reader config', filter='JSON (*.json)')
                if not fp:
                    return
            with open(fp, 'r') as f:
                cfg = json.load(f)
            self.reader_config_path = fp
            self._populate_form(
                self.reader_form, self.reader_widgets, self.reader_types, cfg,
                skip_keys=("file_reader", "files"))

        def load_output_config(self, default=False):
            if default:
                fp = os.path.join(os.path.dirname(__file__),
                                  'settings', 'output_settings_default.json')
            else:
                fp, _ = QFileDialog.getOpenFileName(
                    self, 'Open output config', filter='JSON (*.json)')
                if not fp:
                    return
            with open(fp, 'r') as f:
                cfg = json.load(f)
            self.output_config_path = fp
            self._populate_form(
                self.output_form, self.output_widgets, self.output_types, cfg)

        def _collect_form(self, widgets, types):
            cfg = {}
            for key, widget in widgets.items():
                t = types[key]
                if isinstance(widget, QCheckBox):
                    cfg[key] = int(widget.isChecked()) if t is bool else widget.isChecked()
                else:
                    txt = widget.text()
                    if t is list:
                        cfg[key] = [p.strip() for p in txt.split(',') if p.strip()]
                    elif t is int:
                        try:
                            cfg[key] = int(txt)
                        except ValueError:
                            cfg[key] = 0
                    elif t is float:
                        try:
                            cfg[key] = float(txt)
                        except ValueError:
                            cfg[key] = 0.0
                    else:
                        cfg[key] = txt
            return cfg

        def run_clicked(self):
            reader_cfg = self._collect_form(self.reader_widgets, self.reader_types)
            output_cfg = self._collect_form(self.output_widgets, self.output_types)

            files = [f for f in self.file_edit.text().split(';') if f]
            reader_cfg["files"] = files
            reader_cfg["file_reader"] = self.reader_combo.currentText()

            reader_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='_reader.json')
            json.dump(reader_cfg, reader_tmp)
            reader_tmp.close()

            output_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='_output.json')
            json.dump(output_cfg, output_tmp)
            output_tmp.close()

            self.result = {
                "label_mode": self.label_cb.isChecked(),
                "reader_config": reader_tmp.name,
                "output_config": output_tmp.name,
                "check_manual_labels": self.check_manual_cb.isChecked(),
                "load_labels": self.load_labels_edit.text(),
            }

            self.close()

    app = QApplication([])
    win = SettingsWindow()
    win.show()
    app.exec_()
    return win.result


def get_from_settings_files():
    """Placeholder for future expansion when settings files require
    preprocessing. Currently this function simply returns ``None``."""
    return None


if __name__ == "__main__":

    # Set-up arge parser
    #Decsriptions for all pass-in parameters are provided in their declaration under <help>
    parser = argparse.ArgumentParser(
        prog="RS-PL",
        description=
        "Remote Sensing - Pixel Label (RS-PL) tool:\n This tool was developed to have an easy, quick, and accesible tool to label imagery from various remote sensing platforms.",
        epilog=
        'Tool is currently under developement. For more information, goto https://github.com/jdn8608/SALT'
    )

    # Required arguments
    parser.add_argument(
        'parameter_mode',
        help=
        """Tells the software in what mode to receive option selections from the user.
                        Valid string options are 'GUI'(G) or 'COMMAND'(C), where the letters in parenthesis can be used for shortened indicators.
                        GUI mode opens a GUI interface for the users to select options.\n
                        COMMAND mode retrieves setting selections from the user from the command line arguments and the config files provided under the attriburtes --reader_config --vis_config
                        --output_config list below\n""",
    )

    # Optional arguments
    parser.add_argument(
        '-m',
        '--label_mode',
        help=
        "flag to set the tool in label mode. If not set, tool will be in review only mode. See README for more details",
        action='store_true')
    parser.add_argument(
        '-r',
        '--reader_config',
        help=
        "Path to a JSON file for additional information to use by the instrument file reader, if it is needed."
    )
    parser.add_argument(
        '-v',
        '--vis_config',
        help=
        "Path to a JSON file for additional information and options to use by the visualization script/software.",
        default='./settings/default_vizconfig.json')

    parser.add_argument(
        '-o',
        '--output_config',
        help=
        "file containing the output settings to save the labels created by the user. See the README for more details.",
        default='./settings/output_settings_default.json')
    parser.add_argument(
        '-c',
        '--check_manual_labels',
        help=
        "Flag to check for if manual labels already exists, based on the OUTPUT_SETTINGS_FILE settings. If a file is found, these labels will be loaded as an additional layer. If no file is found, this flag does nothing.",
        action='store_true')
    parser.add_argument(
        '-l',
        '--load_labels',
        help=
        "Pass in argument to select what labels to load into the Editing layer. Values can be 'mask' or 'manual'. If not provided, Editing layer will be loaded with 1s or 0s. IF mask is selected: the file reader needs to return the mask and load_labels=True. IF manual selected, the -l parameter needs to be passed and the file needs to be detected. If either case fails, default settings of None are selected.",
        default=None)
    parser.add_argument('-V', '--verbose', action='store_true')

    # Compile args passed in from the command line by the user
    args = parser.parse_args()
    settings_mode = args.parameter_mode.upper()
    if settings_mode in ('G', 'GUI'):
        gui_args = get_from_GUI()
        if gui_args is None:
            raise SystemExit(0)
        args.label_mode = gui_args["label_mode"]
        args.reader_config = gui_args["reader_config"]
        args.output_config = gui_args["output_config"]
        args.check_manual_labels = gui_args["check_manual_labels"]
        args.load_labels = gui_args["load_labels"]
    elif settings_mode in ('C', 'COMMAND'):
        pass
    else:
        raise Exception(
            "Invalid 'settings_mode' attribute value"
            "Please refer to --help for valid options")

    # Call get_data() to get the data to visualize. This calls the correct instrument filereader module to ingest the data
    # The filereader will create a formatted dict for the ingested data -> data_layer_dict
    output_file_info, views, angles, data_layer_dict, shape, ancillary_config, \
        scene_attrs, review_csv_filepath, review_data, notes = get_data(
            output_settings_filepath=args.output_config,
            reader_config_filepath=args.reader_config,
            label_mode=args.label_mode,
            load_prior_manual_labels=args.check_manual_labels)

    # Call create_tool to create and open the application
    create_tool(args.label_mode,
                data_layer_dict,
                shape,
                output_file_info,
                views,
                angles,
                ancillary_config,
                scene_attrs,
                review_csv_filepath,
                review_data,
                notes,
                load_labels_name=args.load_labels if args.label_mode else '',
                config_filepath=args.vis_config)
