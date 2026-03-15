# IIHS automated script for dynamic belt position calculation

## Intended Use, Scope, and Licensing

This project is licensed under the Apache License, Version 2.0.

This software is intended for use only with data generated according to
Insurance Institute for Highway Safety (IIHS) protocols.

The software has been developed and validated exclusively for IIHS-defined
procedures, assumptions, and data structures. Any use other than 
IIHS-defined procedures, assumptions and data structures is not validated 
or supported.

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IIHS DISCLAIMS ALL 
WARRANTIES, EXPRESS OR IMPLIED, INCLUDING ANY WARRANTIES ARISING FROM 
COURSE OF DEALING, COURSE OF PERFORMANCE, OR USAGE OF TRADE. IIHS 
SPECIFICALLY DISCLAIMS ANY IMPLIED WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE, TITLE, AND NON-INFRINGEMENT. 
USER ACKNOWLEDGES THAT THE SOFTWARE IS PROVIDED “AS IS,” “AS AVAILABLE,” 
AND AT USER’S SOLE RISK. FOR THE AVOIDANCE OF DOUBT, IIHS IS NOT 
RESPONSIBLE FOR ANY BUSINESS DECISIONS MADE BY THE USER IN RELIANCE 
UPON THIS SOFTWARE.
## Overview

This Python pipeline calculates the dynamic belt position for the Hybrid III 5th percentile female dummy in moderate overlap frontal test using pressure sensor and coordinate measurement machine (CMM) data.

_Version: 0.1.0_

## Methodology

At each frame, after cleaning the data, the script identifies the left and right edge points of the belt pressure impression by ensuring that this edge is not an isolated point and a part of the belt impression. The script goes through multiple iterations to refine these edge points to remove any possible outliers and create clean left and right edges. Finally, it averages the cleaned left and right edges to identify the belt centerline. The vertical distance from the chest potentiometer to this belt centerline is calculated to get the raw belt position (unfiltered) at each frame.

## Environment Setup

### Requirements

- Python 3.11
- Dependencies in `requirements.txt`

### Required inputs

1. **CMM Data**

   `Left Rear Passenger.xlsx` file containing pressure sensor and chest potentiometer location:

   - Sheet: `Pressure sensor baseline`
     - Columns: `Row`, `Column`, `X`, `Y`, `Z`
   - Sheet: `Dummy thorax coordinate system`
     - Chest potentiometer coordinates (x, y, z)

2. **Sternum Deflection Data**

   `Chest deflection.xlsx` file containing:

   - Sheet: `Sheet1`
   - Columns:
     - `time` (seconds)
     - `chest deflection`

   > **Note:** This file is automatically deleted after being consumed by the belt position script.

3. **Pressure Sensor Data**

   A folder with CSV files containing pressure data. Pressure sensor data should be recorded at 3300 Hz.

   Export settings for XSensor HSI software:
    - Export frame containing time 0
    - Pressure units as `kPa` or `bar`.
    - CSV format
    - One file per frame (Export -> CSV / Text Options -> Seperate file for each frame)
    - Time format as `HH:mm:ss:LLLLLL` (Options -> Units & Statictics -> Units & Formats -> Time Format)
    - Time as `Elapsed Session Seconds` (Export -> CSV / Text Options -> Date / Time Fields -> Elapsed Session Seconds)

See `templates/` for example excel files.

This package currently assumes the following folder structure:

```bash
<data-path>/
└── <test-id>/
    └── DATA/
        ├── XSENSOR/
        │   └── Rear/
        │       ├── Frame data/ # Frame data CSV files here
        │       └── Belt Position Debug/ # Package side-effects and debug files here
        └── EXCEL/ # Chest deflection and baseline Excel files here
```

### Outputs

- The primary output of this script is the raw/unfiltered dynamic belt position channel, interpolated to a uniform sampling rate of 10 kHz → `Rear/Frame data/Belt Position Debug/interpolated_belt_chest_data.xlsx`

  > **Note:** The subsequent filtering of this interpolated raw channel using channel frequency class 60 (SAE International, 2014), and the calculation of chest index and other evaluation metrics (Moderate Overlap 2.0 rating guidelines Version III, February 2026), are performed in DIAdem as separate processes outside of the current script.
- Dynamic belt position animation → `EXCEL/`

## Usage

### Installation

 Install the package using Python 11.x in Powershell

```powershell
cd path\to\folder\dynamic-belt-position
```

```powershell
& "path\to\Python311\python.exe" -m pip install -e .
```

### Basic usage

In a terminal inside the project folder:

```powershell
& "path\to\Python311\python.exe" -m src.belt_position.main `
  --test-id TEST_ID `
  --data-path "PATH_TO_PARENT_FOLDER_CONTAINING_TESTS"

```

#### Required Arguments

| Argument      | Description                                    |
| ------------- | ---------------------------------------------- |
| `--test-id`   | Name of the test folder containing input files |
| `--data-path` | Root directory containing test folder          |

### Advanced usage

```powershell
& "path\to\Python311\python.exe" -m src.belt_position.main `
  --test-id "TEST_ID" `
  --data-path "PATH_TO_PARENT_FOLDER_CONTAINING_TESTS" `
  --start-time 0.0 `
  --end-time 0.125 `
  --pressure-threshold 20 `
  --pressure-unit kPa `
  --minimum-points 5 `
  --speckle-diff 500 `
  --speckle-ratio 10

```

#### Optional Arguments

| Argument               | Default        | Description                                               |
| ---------------------- | -------------- | --------------------------------------------------------- |
| `--start-time`         | 0.00           | Start time (seconds) for processing window                |
| `--end-time`           | 0.125          | End time (seconds) for processing window                  |
| `--pressure-threshold` | 20             | Minimum pressure value to consider a sensel valid         |
| `--pressure-unit`      | kPa            | Unit of pressure threshold (`kPa` or `bar`)               |
| `--minimum-points`     | 5              | Minimum number of points required to define a belt edge   |
| `--speckle-diff`       | 500            | Maximum allowable pressure difference for speckle removal |
| `--speckle-ratio`      | 10             | Ratio threshold for identifying pressure speckle noise    |

## Project structure

```bash
xsensor-belt-position/
├── src/
│   └── belt_position/
│       ├── algorithm/
│       │   ├── belt_position/
│       │   │   ├── calculate_raw_metrics.py
│       │   │   ├── clean_edge_points.py
│       │   │   ├── detect_edges.py
│       │   │   ├── ensure_consistent_direction.py
│       │   │   ├── estimate_belt_position.py
│       │   │   └── fit_edge_line.py
│       │   ├── data_cleaning/
│       │   │   ├── clean_frame_data.py
│       │   │   ├── process_speckles.py
│       │   │   └── remove_outlier_frames.py
│       │   ├── signal_processing/
│       │   │   ├── interpolate_belt_position.py
│       │   │   ├── merge_belt_and_chest_data.py
│       │   │   └── trim_channels.py
│       │   ├── units/
│       │   │   └── resolve_pressure.py
│       │   ├── visualization/
│       │   │   └── animate_estimated_belt_position.py
│       │   ├── workflow/
│       │   │   └── driver.py
│       ├── config/
│       │   ├── settings.py
│       ├── services
│       │   ├── data_loading/
│       │   │   ├── discover_data.py
│       │   │   ├── load_data.py
│       │   │   └── merge_baseline_frame_data.py
│       │   ├── cleanup.py
│       │   ├── exceptions.py
│       │   ├── logging_service.py
│       │   └── sanitize_data.py
│       └── main.py
├── templates/
│   ├── baseline_file
│   ├── chest deflection file
│   └── frame_file
├── .gitignore
├── Inputs guide.md
├── pyproject.toml
├── README.md
└── requirements.txt
```
