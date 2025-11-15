# BHTOM Differential Photometry Pipeline

A Python pipeline for downloading and processing photometric data from the [BHTOM (Black Hole TOM)](https://bh-tom2.astrolabs.pl/) database, specialized in **differential photometry** for stationary celestial objects such as variable stars, eclipsing binaries, and transiting exoplanets.

## 🎯 Purpose

This pipeline automates the process of:
- Downloading PSF photometry data from BHTOM API
- Cross-matching observations across multiple epochs
- Performing differential photometry using comparison stars
- Generating light curves and diagnostic plots
- Comparing results with aperture photometry

**Target objects:** Variable stars, eclipsing binary systems, transiting exoplanets, and other objects with **constant celestial coordinates**.

> **Note:** Asteroid/moving object functionality is currently disabled as BHTOM does not yet provide tracking data for moving targets.

## 📋 Features

- ✅ **Automated data retrieval** from BHTOM API
- ✅ **PSF photometry** processing with cross-matching
- ✅ **Differential photometry** (target - comparison stars)
- ✅ **Quality control** plots with optimized scales for shallow transits
- ✅ **Comparison** with external aperture photometry
- ✅ **DSS field visualization** with object marking
- ✅ **Multiple output formats** (CSV, space-separated with flux or magnitude)

## 🛠️ Requirements

- Python 3.8+
- Required packages (see `requirements.txt`):
  ```
  requests
  pandas
  astropy
  python-dateutil
  matplotlib
  ```

## 📦 Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd bhtom_photometry
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API credentials** (Required for data download):
   
   Copy the example configuration:
   ```bash
   cp config.py.example config.py
   ```
   
   Edit `config.py` and add your BHTOM API credentials.
   
   **To obtain credentials:** Contact BHTOM administrators at https://bh-tom2.astrolabs.pl/
   
   See [SETUP.md](SETUP.md) for detailed configuration instructions.

## 🚀 Quick Start

### Step 1: Prepare Object Coordinates

Create or edit `objects.dat` with your target and comparison stars (RA and Dec in decimal degrees):

```
Target,318.7370317,-55.8719860
Comp1,318.6979386,-55.8612412
Comp2,318.6808985,-55.7915780
```

### Step 2: Download Data from BHTOM

```bash
python get_data_bhtom.py <OBJECT_NAME> --mjd-range <MJD_MIN> <MJD_MAX>
# or
python get_data_bhtom.py <OBJECT_NAME> --days <NUMBER_OF_DAYS>
```

**Example:**
```bash
python get_data_bhtom.py WASP-46 --mjd-range 60826 60828
```

This downloads photometry data and saves it to `data/photometry_data.pkl`.

### Step 3: Process Photometry

```bash
# Process all filters
python process_photometry.py

# OR process specific filter only
python process_photometry.py --filter R
python process_photometry.py --filter V
python process_photometry.py -f g
```

**Options:**
- `--filter <name>` or `-f <name>`: Process only specific filter (e.g., R, V, I, g, r, i)
- `--ylim-sigma <value>`: Y-axis range in plots (median ± value × σ), default: 3.0

This performs:
- Filtering by photometric band (if specified)
- Cross-matching of objects across epochs
- Differential photometry (Target - Comp1, Target - Comp2)
- Quality checks (Comp1 - Comp2 stability)

**Output files:**
- `output/photometry_results.csv` - Full results with coordinates and magnitudes
- `plots/magnitude_ratios.png` - Diagnostic plots optimized for transit detection

### Step 4: (Optional) Compare with Aperture Photometry

If you have aperture photometry data (e.g., from AstroImageJ):

```bash
python compare_photometry.py
```

**Output:** `plots/photometry_comparison.png` - Comparison between PSF and aperture photometry

### Step 5: (Optional) Visualize Field

```bash
python plot_dss_field.py
```

**Output:** `plots/dss_field.png` - DSS image with marked objects

## 📊 Output Formats

### 1. Standard CSV Format
`output/photometry_results.csv` contains:
- `MJD` - Modified Julian Date
- `TARGET_RA`, `TARGET_DEC` - Measured coordinates
- `TARGET_SEP` - Separation from expected position (arcsec)
- `TARGET_MAG`, `TARGET_MAGERR` - Instrumental magnitude and error
- `COMP1_MAG`, `COMP2_MAG` - Comparison star magnitudes

### 2. Differential Magnitude Format
Convert to differential magnitudes:
```bash
python convert_to_diffmag.py
```

**Output:** `output/photometry_results_diffmag.dat`
```
#JD_UTC    diff_mag    error_diff_mag
2460827.802424    0.623800    0.002100
```

### 3. Flux Format
Convert to flux units:
```bash
python convert_to_flux.py
```

**Output:** `output/photometry_results_flux_simple.dat`
```
#JD_UTC    flux_source    error_flux_source
2460827.802424    2.287494e-05    4.424406e-08
```

## 📂 Project Structure

```
bhtom_photometry/
├── get_data_bhtom.py           # Download data from BHTOM API
├── process_photometry.py       # Main photometry processing pipeline
├── compare_photometry.py       # Compare PSF vs aperture photometry
├── plot_dss_field.py           # Generate DSS field visualization
├── convert_to_diffmag.py       # Convert to differential magnitude format
├── convert_to_flux.py          # Convert to flux format
├── objects.dat                 # Target and comparison star coordinates
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── data/                       # Downloaded photometry data (generated)
│   └── photometry_data.pkl
├── output/                     # Processed results (generated)
│   ├── photometry_results.csv
│   ├── photometry_results_diffmag.dat
│   └── photometry_results_flux*.dat
└── plots/                      # Generated plots (generated)
    ├── magnitude_ratios.png
    ├── photometry_comparison.png
    └── dss_field.png
```

## 🔧 Configuration

### BHTOM API Configuration

The BHTOM API configuration is in `get_data_bhtom.py`:
- **API Base URL:** Configured in `config.py` (default: `https://bh-tom2.astrolabs.pl/common/api/`)
- **Authentication:** Token-based (configured via `config.py` or environment variables)

### Photometry Parameters

In `process_photometry.py`:
- `--filter`: Filter/band selection (e.g., R, V, I, g, r, i). If not specified, all filters are processed
- `--ylim-sigma`: Y-axis plot range factor (median ± factor × σ), default: 3.0
- `max_distance`: Maximum matching radius (default: 5.0 arcsec)
- Cross-matching uses astropy `SkyCoord` for accurate coordinate matching

**Note:** The BHTOM API does not support filter selection during data download. All available filters are downloaded, and filtering is performed during processing.

## 📈 Example: WASP-46 Transit Analysis

This example demonstrates analyzing a transit of the hot Jupiter WASP-46b:

1. **Prepare coordinates** (`objects.dat`):
   ```
   Target,318.7370317,-55.8719860
   Comp1,318.6979386,-55.8612412
   Comp2,318.6808985,-55.7915780
   ```

2. **Download data** (night of May 31/June 1, 2025):
   ```bash
   python get_data_bhtom.py WASP-46 --mjd-range 60826 60828
   ```
   Result: 79 epochs downloaded

3. **Process photometry** (R-band only):
   ```bash
   python process_photometry.py --filter R
   python process_photometry.py
   ```
   Result: High-precision differential light curves with σ ~ 0.01 mag

4. **Results:**
   - Clear detection of shallow transit (~0.02 mag depth)
   - Stable comparison stars (σ < 0.006 mag)
   - Excellent agreement with aperture photometry (offset = 0.797 ± 0.004 mag)

## 🔬 Quality Checks

The pipeline includes several quality control features:

1. **Separation Check:** Reports distance between measured and expected positions
2. **Comparison Star Stability:** Monitors Comp1-Comp2 to detect systematic errors
3. **Multiple Comparison Stars:** Uses two independent comparison stars for verification
4. **Optimized Plot Scales:** Y-axis ranges optimized for shallow transit detection (±0.05 mag)

## 🐛 Known Limitations

- **Moving targets not supported:** BHTOM does not currently provide ephemerides for asteroids
- **Manual comparison star selection:** Users must identify suitable comparison stars
- **Single-filter analysis:** Currently processes one filter at a time

## 📝 Citation

If you use this pipeline in your research, please acknowledge:
- **BHTOM Database:** [https://bh-tom2.astrolabs.pl/](https://bh-tom2.astrolabs.pl/)
- This pipeline (link to your repository)

## 👥 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📄 License

[Specify your license here - e.g., MIT, GPL-3.0, etc.]

## 📧 Contact

[Your contact information or link to issues page]

## 🙏 Acknowledgments

- BHTOM team for providing the photometric database and API
- Astropy community for excellent astronomical Python tools

---

**Version:** 1.0  
**Last Updated:** November 2025
