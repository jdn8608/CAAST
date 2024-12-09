[![Contributors][contributors-shield]][contributors-url]
[![Issues][issues-shield]][issues-url]
[![Unlicense License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]


# PL-RS: Satellite Data Visualization and Pixel Labeling Toolkit

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
**PL-RS** (Pixel Labeling for Remote Sensing... name is a work in progres) is a versatile Python-based tool designed to make it easier for scientists to process, visualize, and label satellite data. The tool allows for handling data from multiple satellite imagers and provides functionality for visualization and pixel-based labeling, which can be used for creating training datasets for AI models.

### Key Features:
- **Universal Satellite Data Compatibility**:
  - Open satellite images from various instruments (e.g., MAIA, MODIS, MISR) using pre-built or user-defined file reader scripts.
  - Easily extend support for additional imagers by following guidelines provided in section <b>INSERT</b>

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
- Python 3.7 or later
- Conda or a Python virtual environment for dependency management

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/jdn8608/PL-RS.git
   cd PL-RS
   ```

2. Install dependencies using Conda:
   ```bash
   conda env create -f environment.yml
   conda activate pl-rs
   ```

3. Alternatively, install dependencies via pip:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Repository Structure
```bash 
.
├── LICENSE
├── README.md
├── __pycache__
│   ├── get_numpy_data.cpython-310.pyc
│   ├── get_numpy_data.cpython-312.pyc
│   └── visualize.cpython-312.pyc
├── environment.yml
├── file_readers
│   ├── MAIA.py
│   ├── MISR.py
│   ├── MODIS.py
├── get_numpy_data.py
├── licenses
│   └── Napari-BSD-3-Clause.txt
├── pl2.py
├── util_files
│   ├── MAIA_ma.json
│   ├── MAIA_readerconfig_1.json
│   ├── MAIA_readerconfig_2.json
│   ├── MAIA_sv.json
│   ├── custom_colormaps.json
│   ├── default_vizconfig.json
│   └── output_settings_default.json
├── visualize.py
└── widgets
    ├── LayerMinMaxSlider.py
    ├── LegendWidget.py
    ├── PointOfViewNavigator.py
    ├── SelectionMinMaxSlider.py
    ├── SubmitButtons.py
    ├── colormaps.py
    ├── create_sliders.py
    └── read_write_outputs.py
```


### Running the Main Tool
To process, visualize, and label satellite data, run the main script `pl2.py`:
```bash
python pl2.py --config <config.json>
```
- **Arguments**:
  - `--config`: A JSON file that specifies the input file paths, search keys, and processing settings.
- **Workflow**:
  - Reads and processes input data using the appropriate file reader.
  - Generates outputs, including visualizations and labeled datasets.

## Adding a New File Reader

To support a new satellite instrument, follow these steps to create a file reader script. Refer to the `MAIA.py` file for an example.

### File Reader Requirements
1. **File Structure and Location**:
   - Place the new file reader in the `file_readers/` directory.
   - Name the file descriptively (e.g., `NEW_INSTRUMENT.py`).

2. **Define `read` Function**:
   - Implement a `read()` function that processes the instrument's data format and returns a NumPy array.
   - Example Inputs:
     - `parent_dir`: Base directory containing the data files.
     - `search`: File search pattern.
     - `view`: View identifier (e.g. for MISR: AN, DA, CF, etc.). Note this is unneeded if your instrument has a only single-view.
     - `bands_to_get`: Bands to extract from the data file.
     - `config`: Additional configuration parameters necessary.
   - Example Outputs:
     - Multi-dimensional arrays representing the satellite data (e.g., bands, angles).

3. **Integration**:
   - Add the new file reader to `get_numpy_data.py` in the `reader_dict`:
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
- [ ] Review-only Mode
    - [ ] Approve/Deny Labeling
    - [ ] RGB Visualization
    - [ ] Notes Widget Development 
    - [ ] Fix Multi-Angle brightness Adjustments for MAIA
- [ ] New Widgets 
    - [ ] "Object" Selection Tool
    - [ ] MAIA Distance to Threshold Compatability
    - [ ] Train/Apply ML Models (RF, DNN, CNN, etc.)

---

## License
This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for more information.

## Contact 
Joseph Nied - jdnied2@illinois.edu - https://climas.illinois.edu/directory/profile/jdnied2 


Project Link: [https://github.com/jdn8608/PL-RS](https://github.com/jdn8608/PL-RS)

## Acknowledgments
Acknowledge Napari & NASA Funding

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/jdn8608/PL-RS
[contributors-url]: https://github.com/jdn8608/PL-RS/contributors 

[issues-shield]: https://img.shields.io/github/issues/jdn8608/PL-RS
[issues-url]: https://github.com/jdn8608/PL-RS/issues

[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/jdn8608/PL-RS/blob/main/LICENSE 

[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/joseph-nied-1621bb1a2
