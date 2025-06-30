# Getting Started

This guide summarises the basic steps to set up the environment and run SALT from the command line.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/jdn8608/SALT.git
   cd SALT
   ```
2. Create and activate the conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate pl2
   ```

## Running the Tool
Launch the application by executing `src/run.py` with the desired parameters:
```bash
python src/run.py [-h] [-m] [-o OUTPUT_SETTINGS_FILE] [-r READER_CONFIG] [-v VIS_CONFIG] [-c] [-l LOAD_LABELS] [-V] dir instrument_name
```
Consult `python src/run.py -h` for detailed explanations of each argument.

