# NOVANA Vegetation Analyzer

A comprehensive Streamlit application for analyzing vegetation data from the Danish National Monitoring and Assessment Programme for the Aquatic and Terrestrial Environment (NOVANA). This tool enables network-based analysis of plant communities, creating visual maps of species relationships and ecological patterns.

## 🌿 Overview

The NOVANA Vegetation Analyzer transforms complex vegetation monitoring data into intuitive network visualizations, where species are positioned based on their co-occurrence patterns. This creates an "ecological landscape" that reveals community structures, species associations, and temporal changes in vegetation composition.

## 🚀 Features

### Core Functionality
- **Data Import & Management**: Import NOVANA monitoring data, species taxonomy, and Ellenberg indicator values
- **Advanced Filtering**: Filter by habitat types, time periods, species characteristics, and geographic regions
- **Network Analysis**: Create species co-occurrence networks using graph theory algorithms
- **Interactive Mapping**: Generate visual maps showing species relationships and ecological gradients
- **Temporal Analysis**: Track changes in vegetation communities over time
- **Dark Diversity Analysis**: Identify missing species that could potentially occur at sites
- **Species Profiles**: Detailed analysis of individual species characteristics and distributions
- **Ecological Indicators**: Analyze environmental conditions using Ellenberg values

### Key Analytical Tools
- Species co-occurrence network construction
- Graph layout optimization (Fruchterman-Reingold algorithm)
- Community detection (Leiden and Louvain algorithms)
- Spatial pattern analysis (Clark-Evans R statistic)
- Kernel density estimation for distribution mapping
- Temporal change detection with statistical significance testing
- Integration with Atlas Flora Danica for enhanced species pools

## 📋 Requirements

### Python Dependencies
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

### Data Requirements
- **NOVANA data**: CSV file with vegetation monitoring records (`novana_data.csv`)
- **Taxa data**: Excel file with species taxonomy and traits (`taxa.xlsx`)
- **Flora Danica data**: Optional CSV file with additional species occurrences (`floradanica.csv`)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/flemmingskov/novanaMap.git
cd novanaMap
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

## 🚦 Getting Started

1. **Launch the application**:
```bash
streamlit run home.py
```

2. **Initial Setup**:
   - On first run, specify a project directory (separate from the application folder)
   - The app will create necessary subfolders automatically in your chosen project location

3. **Data Preparation**:
   - Place your data files in the `data` folder within your project directory:
     - `novana_data.csv`: Main vegetation monitoring data
     - `taxa.xlsx`: Species taxonomy and traits
     - `floradanica.csv`: Optional Atlas Flora Danica data

## 📊 Workflow

The analysis follows a structured workflow with multiple modules:

### Data Management
1. **Import Data** (`1_data_import.py`) - Load NOVANA monitoring data, species taxonomy, and ecological indicators
2. **Apply Filters** (`2_data_filter.py`) - Filter data by habitat types, time periods, species characteristics, and geographic regions

### Graph Construction
3. **Network Analysis** (`3_graph_layout.py`) - Generate species co-occurrence networks and calculate optimal graph layouts
4. **Assign Rare Species** (`4_graph_rare_species.py`) - Include species not captured in the main network analysis
5. **Prepare Map** (`5_graph_prepare_map.py`) - Combine network coordinates with occurrence data to create mappable datasets

### Mapping & Visualization
6. **Create Species Maps** (`6_map_species.py`) - Generate species distribution maps and environmental gradient visualizations
7. **Create Habitat Maps** (`7_map_plots.py`) - Visualize plot-level patterns and temporal changes

### Analysis
8. **Species Temporal Analysis** (`8_analysis_species.py`) - Analyze individual species characteristics and changes over time
9. **Habitat Temporal Analysis** (`9_analysis_plots.py`) - Analyze temporal changes in vegetation communities at the plot level
10. **Dark Diversity Analysis** (`10_analysis_dark_diversity.py`) - Compare local vs regional species pools to identify missing species

## 📁 Project Structure

### Application Structure (where you install the code)
```
novanaMap/
│
├── home.py                  # Main application entry
├── pages/                   # Analysis modules
│   ├── 1_data_import.py
│   ├── 2_data_filter.py
│   ├── 3_graph_layout.py
│   ├── 4_graph_rare_species.py
│   ├── 5_graph_prepare_map.py
│   ├── 6_map_species.py
│   ├── 7_map_plots.py
│   ├── 8_analysis_species.py
│   ├── 9_analysis_plots.py
│   └── 10_analysis_dark_diversity.py
│
├── settings.txt             # Project configuration (points to project folder)
└── requirements.txt         # Python dependencies
```

### Project Data Structure (your chosen project directory)
```
your_project_folder/
│
├── data/                    # Input data files
├── queries/                 # Filtered datasets
├── reference_maps/          # Network coordinate files
├── overlay_maps/            # Combined map databases
└── figures/                 # Output visualizations
```

## 🔍 Key Concepts

### Network Space vs Geographic Space
- **Network coordinates** represent ecological relationships, not geographic locations
- Species close together frequently co-occur
- Distance indicates ecological dissimilarity
- The center represents common/generalist species
- The periphery contains specialized species

### Ecological Interpretation
- **Centroid shifts**: Changes in average community composition
- **Distribution patterns**: Clustered = homogeneous; Dispersed = heterogeneous
- **Temporal changes**: Track ecological succession and environmental responses
- **Dark diversity**: Missing species that could potentially occur locally

## 📈 Output Examples

The tool generates various outputs including:
- Network visualization maps
- Species distribution plots
- Temporal change analyses
- Environmental gradient maps
- Dark diversity assessments
- Statistical summaries
- Export-ready datasets

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests on the [GitHub repository](https://github.com/flemmingskov/novanaMap).

## 📧 Contact

**Author**: Flemming Skov  
**Email**: flemming.skov@ecos.au.dk  
**Institution**: Aarhus University  
**Profile**: [Aarhus University Profile](https://pure.au.dk/portal/da/persons/flemming-skov(d16e357d-aa51-4bd3-ae16-9059110a3fe8).html)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Danish Environmental Protection Agency for NOVANA data
- Atlas Flora Danica for supplementary species data
- Aarhus University for research support

---

**Version**: 1.3  
**Last Updated**: August 2025