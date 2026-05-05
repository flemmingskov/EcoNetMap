# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git Workflow
- Work directly on main branch
- Do not create feature branches
- Commit directly to main
- Do not use git worktrees — this is a single-developer project and worktrees add unnecessary complexity

## Project Overview

coTopo is a Streamlit-based ecological cartography toolkit that transforms vegetation monitoring data into network-based 2D reference landscapes. It positions species in ecological space based on co-occurrence patterns using Jaccard similarity networks with force-directed layouts and MDS distance correction.

**Primary use case:** Danish NOVANA vegetation monitoring program
**Applicable to:** Any plot-based species occurrence dataset
**Technology:** Python + Streamlit multipage application

## Running the Application

```bash
# Launch the application
streamlit run home.py
```

The application uses a multipage structure where all pages are in the `pages/` directory and automatically appear in Streamlit's sidebar navigation.

## Project Structure Philosophy

**Two-directory system:**
- **Application directory** (`/GitHub/coTopo`): Contains the Python code (this repository)
- **Project directory**: User-specified location containing data and outputs

The project directory path is stored in `settings.txt` (INI format) in the application root. On first run, users configure their project location through the web UI, which creates:
- `data/` - Input data files
- `queries/` - Filtered datasets (SQLite databases)
- `reference_maps/` - Network coordinate files (SQLite databases)
- `overlay_maps/` - Combined map databases (SQLite databases)
- `external_data/` - Additional datasets
- `figures/` - Output visualizations

## Data Architecture

### Input Data Requirements
- **Main vegetation data**: CSV with columns for plot_id, species_id, and temporal information
- **Taxa data**: Excel file (`taxa.xlsx`) with species taxonomy, traits, and Ellenberg indicator values
- **Optional Flora Danica**: CSV with regional species pool data for dark diversity analysis

### Data Flow Through Pipeline
1. **Raw data** (CSV/Excel) → cached as Parquet files for performance
2. **Filtered data** → SQLite databases in `queries/` folder
3. **Network coordinates** → SQLite databases in `reference_maps/` folder with tables:
   - `species_coordinates` - Network positions for each species
   - `metadata` - Analysis parameters and provenance
4. **Overlay maps** → SQLite databases in `overlay_maps/` combining coordinates with occurrence data

### Key Database Schema
Network coordinate databases contain:
- Species identifiers and scientific names
- X/Y coordinates (both force-directed and MDS layouts)
- Community assignments (Leiden/Louvain)
- Distance from network center
- Ellenberg indicator values (L, F, R, N)

## Analysis Workflow & Module Organization

Modules follow a numbered sequence indicating the recommended workflow:

### Phase 1: Data Management (01-03)
- `01_data_import.py` - Import and cache raw data
- `02_data_filter.py` - Apply filters and create query databases
- `03_data_diagnostics.py` - Examine temporal and spatial sampling patterns; identifies biases in habitat representation, species accumulation, and sampling intensity

### Phase 2: Network Construction (11-14)
- `11_network_layout.py` - Core network analysis, creates reference maps using:
  - Jaccard similarity from co-occurrence matrices
  - igraph for network construction
  - Fruchterman-Reingold layout OR Multidimensional Scaling (MDS)
  - Community detection (Leiden/Louvain algorithms)
- `12_network_enhance.py` - Assign coordinates to rare species (not in main network)
- `13_network_validation.py` - Comprehensive validation of reference map quality (Procrustes, Ellenberg gradients, k-NN cross-validation, habitat clustering)
- `14_network_overlay.py` - Combine network coordinates with query data to create overlay databases

### Phase 3: Visualization (21-33)
- `21_view_reference_network.py` - View reference network structure
- `22_view_species.py` - Individual species distribution maps
- `23_view_plots.py` - Plot-level visualizations
- `33_analyse_plots.py` - Visualize plots in ecological and geographic space; density analysis, temporal changes, spatial patterns, and environmental gradients at plot level

### Phase 4: Batch Processing (41)
- `41_map_single_species batch.py` - Batch processing for multiple species

### Staging Modules (misc/)
**Note:** These modules are preliminary and not currently part of the production suite. They are stored in the `misc/` directory (not `pages/`) as staging/experimental features under development.

- `24_view_species_double.py` - Compare two species side-by-side (staging)
- `88_analysis_species.py` - Species temporal analysis (experimental)
- `88_analysis_plots.py` - Habitat temporal analysis (experimental)
- `88_analysis_dark_diversity.py` - Missing species identification (experimental)

## Network Analysis Methodology

### Dual Layout Approach
The toolkit generates TWO coordinate systems for each reference map:
1. **Force-directed layout** (Fruchterman-Reingold): Emphasizes clustering and topological patterns
2. **MDS layout**: Preserves pairwise ecological distances for metric interpretation

Both are stored in the same SQLite database with suffixes `_x`/`_y` (force-directed) and `_mds_x`/`_mds_y`.

### Key Algorithms
- **Jaccard similarity**: Primary metric for species associations (not raw co-occurrence counts)
- **Community detection**: Leiden algorithm (primary) or Louvain
- **Rare species assignment**: Jaccard-weighted average of positioned neighbors
- **Distance metrics**: Euclidean distance from network center indicates ecological specialization

### Critical Parameters
- **Minimum occurrence threshold**: Species must occur in N plots to be included in network
- **Edge weight threshold**: Minimum Jaccard similarity to create network edges
- **Layout seed**: Random seed for reproducibility (networks use stochastic algorithms)
- **Community detection resolution**: Controls granularity of detected communities

## Development Conventions

### Code Style
- All modules have comprehensive docstrings explaining purpose, methodology, and position in workflow
- Streamlit caching (`@st.cache_data`) used extensively for data loading and computations
- Type hints used consistently (from `typing` module)
- Custom CSS embedded in each module for consistent UI styling

### Session State Management
Streamlit session state stores:
- All project directory paths (updated from `settings.txt`)
- Currently loaded databases and their metadata
- User selections that persist across page navigation

### Database Operations
- All SQLite operations use context managers
- Databases include metadata tables documenting analysis parameters
- Timestamps and provenance information stored with all outputs

### Error Handling
- Path validation before file operations
- User-friendly error messages through Streamlit UI
- Graceful degradation when optional data missing

## Important Implementation Notes

### Coordinate System Interpretation
- Network X/Y coordinates are NOT geographic locations
- Distance represents ecological dissimilarity (based on co-occurrence)
- Center = generalist species; periphery = specialist species
- Proximity = frequent co-occurrence

### Reproducibility
- Network layouts are stochastic and require seed-setting for exact reproduction
- Multiple runs with different seeds can validate stability
- Environmental gradients (Ellenberg values) validate ecological meaningfulness

### Performance Considerations
- Parquet caching significantly speeds up data loading
- SQLite databases chosen for efficient querying of large networks
- Streamlit's data caching prevents redundant computation

### Visualization Libraries
- **matplotlib/seaborn**: Primary plotting (species maps, network diagrams)
- **plotly**: Interactive plots where needed
- **igraph**: Network visualization capabilities

## Common Development Tasks

When modifying data import (01):
- Parquet cache files stored in project data folder as `.parquet`
- Cache invalidation requires deleting Parquet files
- Column name validation against expected schema

When modifying network analysis (11):
- Changes to Jaccard calculation affect all downstream analyses
- Network metadata includes complete parameter set for provenance
- Force-directed vs MDS layout choice affects interpretation

When adding visualizations (21-33 series):
- Load overlay database which combines coordinates + occurrences
- Access both layout types via `_x`/`_y` and `_mds_x`/`_mds_y` columns
- Ellenberg values available for environmental gradient overlays

When working with staging/experimental modules (misc/):
- These are preliminary features under development
- Not currently part of the production workflow (not in pages/)
- May have incomplete documentation or testing
- Temporal analysis modules require time period information in occurrence data
- Centroid shifts indicate community composition changes
- Distribution changes measured via multiple metrics

## Dependencies

Core packages (see README for full list):
- `streamlit` - Web application framework
- `pandas`, `numpy` - Data manipulation
- `igraph` - Network analysis
- `leidenalg` - Community detection
- `matplotlib`, `seaborn`, `plotly` - Visualization
- `scikit-learn` - MDS and clustering
- `scipy` - Statistical computations
- `sqlite3` - Built-in database support

## Contact & Attribution

**Author:** Flemming Skov (flemming.skov@ecos.au.dk)
**Institution:** Aarhus University
**Repository:** https://github.com/flemmingskov/coTopo
**License:** MIT
