# EcoNetMap
A network-based analytical framework that translates plant species co-occurrence data into a visual reference landscape where species and their assemblages can be explored, compared, and monitored


# coTopo – Ecological Network Mapping Toolkit

A Streamlit application for network-based ecological cartography. coTopo transforms species co-occurrence data from vegetation monitoring programmes into interpretable 2D reference landscapes, revealing community structures, ecological gradients, and species associations.

Developed and tested using the Danish NOVANA vegetation monitoring programme. Applicable to any plot-based species occurrence dataset.

---

## Overview

coTopo positions species in a two-dimensional ecological space based purely on their co-occurrence patterns. Unlike traditional ordination methods that compress relationships into orthogonal axes, it preserves pairwise species associations directly through a Jaccard similarity network with force-directed and MDS layouts.

The result is an **ecological reference landscape** where:
- Species close together frequently co-occur
- Distance reflects ecological dissimilarity
- The centre contains generalist/common species
- The periphery contains specialist/rare species
- Environmental gradients emerge from the data without being imposed

---

## Requirements

### Python dependencies
```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
scipy>=1.10.0
scikit-learn>=1.3.0
igraph>=0.10.0
leidenalg>=0.9.0
plotly>=5.14.0
sqlite3 (built-in)
```

### Data requirements
- **Vegetation monitoring data**: CSV file with plot-level species occurrence records
- **Taxa data**: Excel file with species taxonomy, traits, and Ellenberg indicator values (`taxa.xlsx`)
- **Regional species pool** *(optional)*: CSV file with regional occurrence data for dark diversity analysis (e.g., Atlas Flora Danica)

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/flemmingskov/coTopo.git
cd coTopo
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

---

## Getting Started

1. **Launch the application**:
```bash
streamlit run home.py
```

2. **Initial setup**:
   On first run, specify a project directory (separate from the application folder). The app creates the necessary subfolders automatically.

3. **Place your data files** in the `data/` subfolder of your project directory:
   - Your vegetation monitoring CSV
   - `taxa.xlsx` — species taxonomy and traits
   - Optional regional species pool CSV

---

## Application Structure

### Two-directory system

| Directory | Purpose |
|---|---|
| Application directory (`coTopo/`) | Python code — this repository |
| Project directory | User-specified — contains data and outputs |

The project directory path is stored in `settings.txt` (INI format) in the application root.

### Project folder layout
```
your_project_folder/
│
├── data/               # Input data files
├── queries/            # Filtered datasets (SQLite)
├── reference_maps/     # Network coordinate files (SQLite)
├── overlay_maps/       # Combined map databases (SQLite)
├── external_data/      # Additional external datasets
└── figures/            # Output visualizations
```

### Application file layout
```
coTopo/
│
├── home.py                        # Main entry point — start here
├── settings.txt                   # Project configuration
├── requirements.txt
└── pages/
    ├── 01_data_import.py          # Import vegetation and taxa data
    ├── 02_data_filter.py          # Filter and create query datasets
    ├── 03_data_diagnostics.py     # Inspect sampling patterns and biases
    ├── 11_network_layout.py       # Build co-occurrence network and reference map
    ├── 12_network_enhance.py      # Assign coordinates to rare species
    ├── 13_network_validation.py   # Validate network quality
    ├── 14_network_overlay.py      # Combine coordinates with occurrence data
    ├── 21_view_reference_network.py  # Visualise reference network structure
    ├── 22_view_species.py         # Individual species distribution maps
    └── 23_view_plots.py           # Plot-level visualisations
```

---

## Workflow

Use the sidebar navigation in the application to work through the following stages in order.

### Phase 1 — Data management (01–03)

**01 Import data**
Load vegetation monitoring data (species × plots), species taxonomy, Ellenberg indicator values, and optionally a regional species pool dataset. Data is cached as Parquet files for performance.

**02 Filter data**
Filter by habitat types, taxonomic groups, time periods, geographic regions, and data quality thresholds. Exports filtered datasets as SQLite databases to the `queries/` folder.

**03 Data diagnostics**
Examine temporal and spatial sampling patterns. Identifies potential biases that could affect network stability or downstream analyses.

### Phase 2 — Network construction (11–14)

**11 Network layout**
Calculates Jaccard similarity from co-occurrence matrices and builds a species association network. Generates two coordinate systems:
- *Force-directed layout* (Fruchterman-Reingold) — emphasises clustering and topological patterns
- *MDS layout* — preserves pairwise ecological distances for metric interpretation

Both are stored in the same SQLite database. Community detection uses the Leiden algorithm (Louvain as alternative).

**12 Network enhancement**
Assigns network coordinates to species that fell below the minimum occurrence threshold and were excluded from the main network. Uses Jaccard-weighted averaging of positioned neighbours.

**13 Network validation**
Assesses network quality and layout stability. Supports comparison across multiple runs with different random seeds.

**14 Network overlay**
Combines network coordinates with occurrence data from a query dataset, creating unified SQLite databases in the `overlay_maps/` folder ready for visualisation.

### Phase 3 — Visualisation (21–23)

**21 View reference network**
Interactive visualisation of the full species network. Hover tooltips, community colouring, and Ellenberg gradient overlays.

**22 View species**
Individual species distribution maps in both ecological space (position in the reference landscape) and geographic space. Includes temporal change analysis and optional regional species pool overlay.

**23 View plots**
Plot-level visualisations in ecological and geographic space. Colours plots by habitat type, environmental indicator values, or monitoring region. Supports temporal trajectory mapping.

---

## Key concepts

### Dual coordinate system
Each reference map stores two layouts:

| Layout | Suffix | Best for |
|---|---|---|
| Force-directed | `_x` / `_y` | Visualising clusters and community structure |
| MDS-corrected | `_mds_x` / `_mds_y` | Interpreting distances as ecological dissimilarity |

### Network space vs geographic space
Network coordinates are **not** geographic locations. A species' position reflects which other species it tends to co-occur with — nothing more. Geographic maps are generated separately by joining occurrence records to the network coordinates.

### Ellenberg indicator values
Species positions in the network can be overlaid with Ellenberg values (light, moisture, reaction, nutrients) to validate that the ecological gradient structure emerging from co-occurrence data is ecologically meaningful.

### Reproducibility
Network layouts are stochastic. Set a random seed for exact reproduction. Running multiple seeds is recommended to assess layout stability before interpreting fine-scale patterns.

---

## Development context

coTopo was developed and tested using:
- **NOVANA** — the Danish National Monitoring and Assessment Programme for the Aquatic and Terrestrial Environment, which provided the primary vegetation monitoring dataset
- **Atlas Flora Danica** — used as the regional species pool for dark diversity analysis in the Danish context

These datasets informed design decisions throughout, but all components of coTopo are dataset-agnostic. Any plot-based species occurrence dataset with compatible column structure can be used.

---

## Contributing

Contributions, issues, and suggestions are welcome on the [GitHub repository](https://github.com/flemmingskov/coTopo).

---

## Contact

**Author:** Flemming Skov
**Email:** flemming.skov@ecos.au.dk
**Institution:** Aarhus University
**Profile:** [Aarhus University](https://pure.au.dk/portal/da/persons/flemming-skov(d16e357d-aa51-4bd3-ae16-9059110a3fe8).html)

---

## Citation

If you use coTopo in your research, please cite:

> Skov, F. (2026). coTopo: Network-based ecological cartography for vegetation analysis. Aarhus University. https://github.com/flemmingskov/coTopo

*Manuscript in preparation for Journal of Vegetation Science.*

---

## Acknowledgements

- Danish Environmental Protection Agency for access to NOVANA monitoring data
- Atlas Flora Danica for supplementary regional species occurrence data
- Aarhus University for research support

---

## License

MIT License — see LICENSE file for details.

---

**Version:** 1.01
**Last updated:** February 2026
