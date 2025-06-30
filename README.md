[![Contributors][contributors-shield]][contributors-url]
[![Issues][issues-shield]][issues-url]
[![Unlicense License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]


# SALT: Satellite-imager Annotation & Labeling Toolkit

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#overview">Overview</a></li>
    <li><a href="#key-features">Key Features</a></li>
    <li><a href="#installation">Installation</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#adding-a-new-file-reader">Adding a New File Reader</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>


## Overview
**SALT** (Satellite-imager Annotation & Labeling Toolkit... name is a work in progres) is a versatile Python-based tool designed to make it easier for scientists to process, visualize, and label satellite data. The tool allows for handling data from multiple satellite imagers and provides functionality for visualization and pixel-based labeling, which can be used for creating training datasets for AI models.

### Key Features:
- **Universal Satellite Data Compatibility**:
  - Open satellite images from various instruments (e.g., MAIA, MODIS, MISR) using pre-built or user-defined file reader scripts.
  - Easily extend support for additional imagers by following the guidelines outlined below.

- **Multi-Angle Visualization**:
  - Supports data visualization for multi-angle imagers, including upcoming missions like MAIA and existing ones like MISR (once developed).

- **Pixel-Based Labeling**:
  - Annotate individual pixels (e.g., for cloud masking) to create high-quality datasets for AI training.
  - Save labeled data in formats compatible with further processing or training pipelines.

- **Interactive Tools**:
  - Integration with Napari for interactive visualization.
  - Custom widgets for adjusting sliders, managing colormaps, navigating points of view, and handling legend creation.

## Installation

### Prerequisites
- Python 3.12 or later
- Conda (or another environment manager) for dependency management

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/jdn8608/SALT.git
   cd SALT
   ```

2. Install dependencies using Conda:
   ```bash
   conda env create -f environment.yml
   conda activate pl2
   ```

## Usage

### Repository Structure
```bash
.
├── LICENSE
├── README.md
├── environment.yml
├── labels/
│   └── csv/
│       └── cloud_mask_review.csv
├── licenses/
│   └── Napari-BSD-3-Clause.txt
└── src/
    ├── file_readers/
    │   ├── MAIA.py
    │   ├── MISR.py
    │   ├── ML_64x64.py
    │   ├── MODIS.py
    │   └── __init__.py
    ├── run.py
    ├── settings/
    │   ├── MAIA_loc.json
    │   ├── MAIA_ma.json
    │   ├── MAIA_proxy.json
    │   ├── ML_64x64.json
    │   ├── custom_colormaps.json
    │   ├── default_vizconfig.json
    │   └── output_settings_default.json
    ├── util/
    │   ├── LayerType.py
    │   ├── colormaps.py
    │   ├── create_tool.py
    │   ├── get_data.py
    │   └── read_write_outputs.py
    └── widgets/
        ├── ControlPanel.py
        ├── GradeSlider.py
        ├── LabelLegendWidget.py
        ├── LayerManager.py
        ├── LayerMinMaxSlider.py
        ├── LegendWidget.py
        ├── LogicGatesPanel.py
        ├── PointOfViewNavigator.py
        ├── SceneLabelGrid.py
        ├── SelectionMinMaxSlider.py
        ├── Sliders.py
        ├── SubmitButtons.py
        ├── ThresholdPanel.py
        ├── ThresholdPanel_old.py
        └── ViewerManagerTab.py
```


### Running the Main Tool
To process, visualize, and label satellite data, run the main script `src/run.py`:
```bash
python src/run.py [-h] [-m] [-o OUTPUT_SETTINGS_FILE] [-r READER_CONFIG] [-v VIS_CONFIG] [-c] [-l LOAD_LABELS] [-V] dir instrument_name
```


**positional arguments:**

<table>
  <thead>
    <tr>
      <th>Parameter</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>dir</code></td>
      <td>Root directory to retrieve files from.</td>
    </tr>
    <tr>
      <td><code>instrument_name</code></td>
      <td>Instrument that we will be reading in data for. This will determine how to read in data (i.e., determine the file reader). See the README for more details.</td>
    </tr>
  </tbody>
</table>

**options:**


<table>
  <thead>
    <tr>
      <th>Optional Parameters</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>--help</code></td>
      <td>show this help message and exit</td>
    </tr>
    <tr>
      <td><code>--label_mode</code></td>
      <td>flag to set the tool in label mode. If not set, tool will be in review only mode. See README for more details</td>
    </tr>
    <tr>
      <td><code>--reader_config&nbsp;READER_CONFIG</code></td>
      <td>Path to a .json file for additional information to use by the instrument file reader, if it is needed.</td>
    </tr>
    <tr>
      <td><code>--output_settings_file&nbsp;OUTPUT_SETTINGS_FILE</code></td>
      <td>file containing the output settings to save the labels created by the user. See the README for more details.</td>
    </tr>
    <tr>
      <td><code>--vis_config&nbsp;VIS_CONFIG</code></td>
      <td>Path to a .json file for additional information and options to use by the visualization script/software.</td>
    </tr>
    <tr>
      <td><code>--check_manual_labels</code></td>
      <td>Flag to check for if manual labels already exists, based on the OUTPUT_SETTINGS_FILE settings. If a file is found, these labels will be loaded as an additional layer. If no file is found, this flag does nothing.</td>
    </tr>
    <tr>
      <td><code>--load_labels&nbsp;LOAD_LABELS</code></td>
      <td>Pass in argument to select what labels to load into the Editing layer. Values can be 'mask' or 'manual'. If not provided, Editing layer will be loaded with 1s or 0s. IF mask is selected: the file reader needs to return the mask and load_labels=True. IF manual selected, the -l parameter needs to be passed and the file needs to be detected. If either case fails, default settings of None are selected.</td>
    </tr>
    <tr>
      <td><code>--verbose</code></td>
      <td>Flag to turn on software activity output to the terminal.</td>
    </tr>
  </tbody>
</table>


## Adding a New File Reader

To support a new satellite instrument, follow these steps to create a file reader script. Refer to the `MAIA.py` file for an example.

### File Reader Requirements
1. **File Structure and Location**:
   - Place the new file reader script in the `src/file_readers/` directory.
   - Name the file descriptively (e.g., `NEW_INSTRUMENT.py`).
   - NEW_INSTRUMENT.py needs to have a read() function (see below for more details. The file can of course have other functions but needs a read() function to be called from get_data()

2. **Define `read` Function**:
   - Implement a `read()` function that processes the instrument's data format with the following inputs:
     - parent_dir : the root (parent) directory to search to find files within
     - search     : a comprehensive string to search for files with a pattern... '*' symbols are wildcards.
     - views      : a list of strings to represent the views for the instrument. If the instrument is not a multi-angle instrument, the list should be of lenght 1.
     - config     : a dictionary of config options that may be useful for your data ingestion for a instrument data.

   - Required Outputs:
     - a "data" dictionary: The keys are the name of the layers to add into the tool. The values are tuple, where entry [0] is a LayerType (see `src/util/LayerType.py`) that indicates how this data layer will be used... entry [1] is a NumPy array of the data layer to be added.
     - a string : that represents the filename of the output file. Should contain sub-string '<view>' if there are multiple views so that each view can be saved out seperately by replacing this sub-string when file writing.
     - a tuple : that represents the NumPy shape for layers that will be added as image layers (not labels)
       
3. **Integration**:
   - Add the new file reader to `src/util/get_data.py` in the `reader_dict`:
   ```python
   reader_dict = {
       "MAIA": file_readers.MAIA.read,
       "NEW_INSTRUMENT": file_readers.NEW_INSTRUMENT.read,
   }
   ```


## Roadmap

- [x] Initial Set-up for Single-view Imagers
    - [x] Min/Max Sliders for Band Data
    - [x] Editable/Non-Editable Label Layers for Cloud Mask(s)
    - [x] Scene Level Qualitative Labels
    - [x] Save/Loading Saved Labels
    - [x] Colormap Settings
- [x] Multi-view Set-up for Single-view Imagers
    - [x] Point of View (POV) Slider widget
    - [x] Integration of POV Slider with all prior functionality
- [x] Review-only Mode
    - [x] Approve/Deny Labeling
    - [x] Notes Widget Development 
- [x] Reading in & Visualizing Meta-data
    - [x] Re-work `read()` for file readers 
    - [x] Adjustments to the visualization pipeline
    - [x] Add metadata attributes to pipeline
- [ ] Visual Additions & Fixes 
    - [ ] RGB Visualization
    - [ ] Grid View Indicators
    - [ ] Grid View Enhancements
- [ ] Tutorial & Manuals 
    - [ ] Outline pictures to describe widgets
    - [ ] Create a tutorial video
    - [ ] Create a user guide manual about the tool
    - [ ] Finish code commenting
- [ ] MAIA Features
    - Fix Brightness Changes in Multi-views 
    - Distance to Threshold Widget
- [ ] New Pixel Labeling Widgets 
    - [ ] "Object" Selection Tool
- [ ] Interface with ML Models
    - [ ] Train/Apply ML Models (RF, DNN, CNN, etc.)

---

## License
This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for more information.

## Contact 
Joseph Nied - jdnied2@illinois.edu - https://climas.illinois.edu/directory/profile/jdnied2 


Project Link: [https://github.com/jdn8608/SALT](https://github.com/jdn8608/SALT)

## Acknowledgments
Acknowledge Napari & NASA Funding

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/jdn8608/SALT
[contributors-url]: https://github.com/jdn8608/SALT/contributors 

[issues-shield]: https://img.shields.io/github/issues/jdn8608/SALT
[issues-url]: https://github.com/jdn8608/SALT/issues

[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/jdn8608/SALT/blob/main/LICENSE 

[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/joseph-nied-1621bb1a2
