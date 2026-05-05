# NOVANA Vegetation Analyzer
## Complete User Manual

**Version 1.3 | August 2025**

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Understanding the Workflow](#understanding-the-workflow)
4. [Data Management](#data-management)
5. [Graph Construction](#graph-construction)
6. [Mapping & Visualization](#mapping--visualization)
7. [Advanced Analysis](#advanced-analysis)
8. [Interpreting Results](#interpreting-results)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Technical Details](#technical-details)

---

## Introduction

### What is the NOVANA Vegetation Analyzer?

The NOVANA Vegetation Analyzer is a comprehensive tool for analyzing vegetation monitoring data from the Danish National Monitoring and Assessment Programme (NOVANA). Unlike traditional species distribution analysis, this tool creates **network-based visualizations** where species are positioned in an "ecological space" based on their co-occurrence patterns.

### Key Concepts

**Ecological Network Space**: Instead of showing where species occur geographically, the tool positions species based on which other species they're found with. Species that frequently co-occur appear close together in this ecological landscape.

**The Center vs. Periphery**: 
- **Center**: Common, generalist species found across many habitat types
- **Periphery**: Specialized species with narrow ecological requirements

**Dark Diversity**: Species that *could* potentially occur at a site based on the regional species pool, but are currently absent.

### Who Should Use This Tool?

- **Ecologists** studying plant community structure and dynamics
- **Conservation biologists** identifying restoration opportunities
- **Environmental consultants** analyzing habitat quality and completeness
- **Researchers** investigating temporal changes in vegetation communities
- **Land managers** planning biodiversity conservation strategies

---

## Getting Started

### Installation

1. **Download the Application**
   ```bash
   git clone https://github.com/flemmingskov/novanaMap.git
   cd novanaMap
   ```

2. **Set Up Python Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Launch the Application**
   ```bash
   streamlit run home.py
   ```

### First Time Setup

When you first run the application, you'll be guided through creating a project structure:

1. **Choose Project Location**: Select where you want to store your data and results (separate from the application folder)
2. **Automatic Folder Creation**: The app creates these folders in your project directory:
   - `data/` - Input files
   - `queries/` - Filtered datasets  
   - `reference_maps/` - Network coordinates
   - `overlay_maps/` - Combined map databases
   - `figures/` - Output visualizations

### Required Data Files

Place these files in your project's `data/` folder:

**Essential Files:**
- `novana_data.csv` - NOVANA monitoring records with species occurrences
- `taxa.xlsx` - Species taxonomy, traits, and Ellenberg indicator values

**Optional but Recommended:**
- `floradanica.csv` - Atlas Flora Danica records for enhanced regional species pools

### Data File Formats

**NOVANA Data (novana_data.csv)**
Required columns:
- `aktId` - Unique plot identifier
- `artId` - Unique species identifier  
- `almindeligtNavn` - Danish common name
- `dato` - Date (YYYYMMDD format)
- `naturtypeId` - Habitat type code
- `UTMx`, `UTMy` - Geographic coordinates

**Taxa Data (taxa.xlsx)**
Required columns:
- `artId` - Species identifier (matching NOVANA data)
- `almindeligtNavn` - Danish common name
- `videnskabeligtNavn` - Scientific name
- `L`, `M`, `N`, `R`, `T` - Ellenberg indicator values
- Additional trait columns as available

---

## Understanding the Workflow

The NOVANA Vegetation Analyzer follows a structured 10-step workflow organized into four main phases:

### Phase 1: Data Management (Steps 1-2)
**Goal**: Import and filter your data to create focused datasets for analysis

### Phase 2: Graph Construction (Steps 3-5)  
**Goal**: Build the ecological network and assign coordinates to all species

### Phase 3: Mapping & Visualization (Steps 6-7)
**Goal**: Create visual maps of species and habitat distributions

### Phase 4: Advanced Analysis (Steps 8-10)
**Goal**: Perform temporal analysis and dark diversity assessment

---

## Data Management

### Step 1: Import Data

**Purpose**: Load your vegetation monitoring data, species information, and ecological indicators into the system.

**What Happens**:
- NOVANA data is loaded and date columns are properly formatted
- Habitat types are automatically classified into major categories
- Taxa data with Ellenberg values and traits is imported
- Flora Danica data is loaded and merged with Danish species names
- All data is cached in optimized Parquet format for faster future loading

**Key Features**:
- **Smart Caching**: After first import, data loads much faster from cache
- **Data Validation**: Checks for required columns and data integrity
- **Automatic Enhancement**: Flora Danica records are enhanced with Danish names from taxa data

**Tips**:
- Use the "Fast Cache" option for subsequent sessions
- Clear cache if you update your source data files
- Check the data preview to ensure proper loading

### Step 2: Apply Filters

**Purpose**: Create focused datasets by filtering species, habitats, time periods, and geographic regions.

**Filtering Options**:

**Taxonomic Filters**:
- **Categories**: Filter by taxonomic level (typically "Art" for species)
- **Major Groups**: Select plant groups (e.g., "Tracheophyta" for vascular plants)
- **Origin Status**: Choose native, non-native, or invasive species

**Habitat Filters**:
- **Major Types**: Select broad habitat categories (forests, grasslands, wetlands, etc.)
- **Specific Habitats**: Fine-tune by removing specific habitat codes
- **Sampling Methods**: Choose data collection methods (pinpoint, plot-based, etc.)

**Temporal and Geographic Filters**:
- **Date Range**: Select specific time periods
- **Random Sampling**: Subsample plots if you have very large datasets

**Export Options**:
- **Basic Export**: Apply minimum occurrence filters to remove rare species
- **Stratified Sample**: Create balanced samples across habitat types  
- **Geographic Subset**: Filter by distance from a center point

**Best Practices**:
- Start with broad filters and gradually narrow down
- For network analysis, include at least 50-100 species
- Balance between data quantity and ecological focus
- Export to SQLite format for best compatibility with subsequent steps

---

## Graph Construction

### Step 3: Network Analysis

**Purpose**: Create the core ecological network that forms the foundation for all subsequent analysis.

**The Process**:

**1. Network Creation**:
- Species become "nodes" in the network
- "Edges" connect species that co-occur in the same plots
- Edge weights represent the frequency of co-occurrence

**2. Layout Generation**:
- Uses the Fruchterman-Reingold algorithm to position species
- Species that co-occur frequently are placed near each other
- The algorithm iteratively optimizes the layout

**3. Community Detection**:
- **Leiden Algorithm**: Identifies clusters of closely associated species
- **Louvain Algorithm**: Alternative clustering method for comparison
- These communities often represent distinct ecological groups

**Parameters to Consider**:
- **Minimum Occurrences**: Filter out very rare species (default: 1)
- **Layout Iterations**: More iterations = better layout but slower (default: 500)
- **Random Seed**: Use fixed seed for reproducible results

**Key Outputs**:
- Species coordinates in ecological space (0-1 scale)
- Network metrics (degree, centrality, clustering)
- Community assignments for each species

### Step 4: Assign Rare Species

**Purpose**: Include species that were filtered out of the main network analysis due to low occurrence numbers.

**How It Works**:
- Identifies species present in your data but missing from the network
- Uses co-occurrence patterns with "core" species to assign coordinates
- Core species are those far enough from the center (distance ≥ threshold)

**Key Parameters**:
- **Distance Threshold**: Minimum distance from center for core species (default: 0.3)
- **Minimum Co-occurrences**: Required shared plots with core species (default: 2)
- **Maximum Neighbors**: Limit on reference species used (default: 10)

**Why This Matters**:
- Ensures comprehensive species coverage
- Prevents loss of ecologically important rare species
- Maintains network integrity while being inclusive

### Step 5: Prepare Map

**Purpose**: Combine network coordinates with occurrence data to create unified databases ready for mapping.

**What Happens**:
- Network coordinates are merged with original species data
- Plot coordinates are calculated as weighted averages of their species
- Ellenberg indicator values are added when available
- Everything is combined into SQLite databases for efficient access

**Coordinate Calculation Methods**:
- **Equal Weighting**: Each species contributes equally to plot position
- **Abundance Weighting**: More abundant species have greater influence
- **Degree Weighting**: More connected species have greater influence

**Key Outputs**:
- `taxa` table: All species with network coordinates and ecological data
- `aktId` table: Plot-level data with calculated coordinates and environmental indicators
- `data` table: Original occurrence records linked to coordinates

---

## Mapping & Visualization

### Step 6: Create Species Maps

**Purpose**: Visualize how species are distributed in ecological space and analyze environmental gradients.

**Map Types Available**:

**1. Species Distribution Maps**:
- Overview of all species positions in ecological space
- Color by taxonomic groups or network communities
- Density overlays show concentration patterns
- Random species labeling for identification

**2. Individual Species Analysis**:
- Detailed view of single species distributions
- Temporal filtering to see changes over time
- Convex hull showing total range
- KDE contours showing core habitat areas
- Geographic maps with UTM coordinates

**3. Environmental Gradient Maps**:
- Visualize Ellenberg indicator patterns
- Light, moisture, pH, nitrogen, and temperature gradients
- Weighted density maps showing environmental preferences
- Value range filtering for focused analysis

**4. Forest Category Maps**:
- Specialized maps for forest plant functional groups
- Shade tolerance and light requirement patterns

**Interpretation Tips**:
- **Center species**: Generalists found across many habitats
- **Peripheral species**: Specialists with narrow requirements
- **Clustered patterns**: Distinct ecological communities
- **Gradient patterns**: Environmental transitions

### Step 7: Create Habitat Maps

**Purpose**: Analyze plot-level patterns, habitat distributions, and temporal changes.

**Map Types Available**:

**1. Plot Distribution Analysis**:
- Show plots colored by habitat type or environmental conditions
- Density analyses reveal habitat concentration patterns
- Background layers show complete dataset context
- Geographic mapping with UTM coordinates

**2. Temporal Change Maps**:
- Compare plot positions between time periods
- KDE contours show shifting habitat distributions
- Centroid movement indicates directional changes
- Statistical analysis of movement significance

**3. Environmental Analysis**:
- Plot-level environmental conditions using Ellenberg values
- Gradient maps show environmental variation across the landscape
- Contour interpolation reveals environmental patterns

**Key Features**:
- **Interactive Filtering**: Dynamically filter by habitat types, regions, and time periods
- **Multiple Visualization Layers**: Combine points, density, and contours
- **Geographic Context**: Link ecological space to real-world locations
- **Export Options**: Save high-resolution maps for publications

---

## Advanced Analysis

### Step 8: Species Temporal Analysis

**Purpose**: Analyze how individual species have changed their distributions and ecological associations over time.

**Analysis Components**:

**1. Distribution Shift Analysis**:
- **Centroid Movement**: Calculate how the average position of a species has shifted
- **Significance Testing**: Bootstrap analysis to test if shifts are statistically significant
- **Distance from Center**: Track whether species are becoming more or less specialized

**2. Density Change Analysis**:
- **KDE Comparison**: Compare probability density surfaces between time periods
- **Total Variation Distance**: Quantify overall distributional change
- **Hotspot Analysis**: Identify areas of gained or lost density

**3. Environmental Change Analysis**:
- **Ellenberg Indicators**: Track changes in light, moisture, pH, nitrogen, and temperature
- **Statistical Testing**: T-tests to identify significant environmental shifts
- **Ecological Interpretation**: Understand what environmental changes mean

**Key Outputs**:
- Movement vectors showing directional changes
- Significance values for all detected changes
- Environmental change summaries with ecological interpretation
- High-resolution maps suitable for publication

**Interpretation Guide**:
- **Significant centroid shifts**: Real changes in species distribution
- **Movement toward center**: Species becoming less specialized
- **Movement toward periphery**: Species becoming more specialized
- **Environmental changes**: Indicate changing habitat conditions

### Step 9: Habitat Temporal Analysis

**Purpose**: Analyze changes in vegetation communities and ecological patterns at the plot/habitat level.

**Analysis Components**:

**1. Community Composition Changes**:
- **Centroid Shift Analysis**: Track how average community composition has changed
- **Bootstrap Testing**: Statistical validation of detected changes
- **Distance and Bearing Changes**: Quantify magnitude and direction of shifts

**2. Ecological Distribution Changes**:
- **KDE Change Analysis**: Compare community distribution patterns over time
- **Hotspot Dynamics**: Identify areas of ecological gain, loss, or stability
- **Total Variation Metrics**: Quantify overall distributional change

**3. Environmental Condition Changes**:
- **Ellenberg Indicator Trends**: Track environmental changes across habitats
- **Statistical Significance**: T-tests for each environmental variable
- **Ecological Interpretation**: Understand environmental drivers of change

**4. Ecological Heterogeneity Analysis**:
- **Clark-Evans R Statistic**: Measure spatial pattern of communities
- **Pattern Classification**: Clustered, random, or dispersed patterns
- **Change Detection**: Track increasing or decreasing heterogeneity

**Key Insights**:
- **Community Shifts**: Are habitats changing their ecological character?
- **Environmental Drivers**: What environmental changes are driving shifts?
- **Heterogeneity Trends**: Is the landscape becoming more uniform or diverse?
- **Restoration Implications**: Where and how can habitats be restored?

### Step 10: Dark Diversity Analysis

**Purpose**: Identify species that could potentially occur at local sites but are currently absent, revealing restoration opportunities and biodiversity potential.

**Core Concept**:
Dark diversity represents the "missing" species from a local community that are present in the regional species pool and could theoretically establish given suitable conditions.

**Analysis Process**:

**1. Species Pool Definition**:
- **Local Pool**: Species actually observed at your study sites
- **Regional Pool**: Species available in the broader landscape
- **Flora Danica Enhancement**: Optionally expand regional pool with Atlas data

**2. Species Classification**:
- **Common Species** (center): Generalist species (distance 0-0.09 from center)
- **Medium Species** (middle): Moderate specialists (distance 0.09-0.45)
- **Specific Species** (periphery): High specialists (distance 0.45-0.5)

**3. Dark Diversity Calculation**:
- For each category, identify species present regionally but absent locally
- Calculate completeness metrics (local richness / regional richness)
- Assess restoration potential for each species group

**4. Flora Danica Integration**:
- Search Atlas Flora Danica records within specified radius of study sites
- Add species found nearby but not in your regional dataset
- Provides more comprehensive picture of potential species

**Key Metrics**:
- **Completeness**: Percentage of regional pool present locally
- **Dark Diversity Size**: Number of potentially missing species
- **Category-Specific Patterns**: Different completion rates for generalists vs. specialists

**Interpretation**:
- **High Completeness (>80%)**: Well-developed communities with few restoration opportunities
- **Medium Completeness (50-80%)**: Moderate restoration potential
- **Low Completeness (<50%)**: High restoration potential, possibly degraded habitat
- **Missing Specialists**: Often indicates habitat quality issues
- **Missing Generalists**: May indicate severe disturbance or young communities

**Restoration Applications**:
- **Priority Species**: Focus on missing species with high local suitability
- **Habitat Requirements**: Use Ellenberg values to understand what conditions are needed
- **Feasibility Assessment**: Consider how to create suitable conditions for missing species

---

## Interpreting Results

### Understanding Ecological Space

**The Coordinate System**:
- **X and Y coordinates**: Range from 0 to 1, representing ecological relationships, not geography
- **Center (0.5, 0.5)**: Common, generalist species found across many habitats
- **Distance from Center**: Indicates ecological specialization
- **Bearing from Center**: Direction in ecological space (no inherent meaning)

**Distance Interpretation**:
- **0.0 - 0.125**: Core generalist species
- **0.125 - 0.25**: Common species with some specialization
- **0.25 - 0.375**: Moderately specialized species  
- **0.375 - 0.5**: Highly specialized species

### Reading the Maps

**Species Distribution Maps**:
- **Tight clusters**: Distinct ecological communities
- **Scattered patterns**: Generalist species or diverse communities
- **Empty areas**: Ecological "gaps" - combinations that don't occur in nature
- **Gradients**: Smooth transitions between community types

**Temporal Change Maps**:
- **Arrow direction**: Direction of ecological change
- **Arrow length**: Magnitude of change
- **Confidence intervals**: Statistical reliability of detected changes
- **Color changes**: Shifts in community composition

**Environmental Gradient Maps**:
- **Color intensity**: Strength of environmental preference
- **Contour lines**: Equal-value boundaries for environmental variables
- **Gradients**: Smooth environmental transitions

### Statistical Significance

**P-values**:
- **p < 0.05**: Statistically significant change (95% confidence)
- **p < 0.01**: Highly significant change (99% confidence)
- **p ≥ 0.05**: No significant change detected

**Bootstrap Testing**:
- Used for temporal change analysis
- Randomly reassigns time periods many times
- Determines if observed changes could occur by chance
- More reliable than simple comparisons

**Effect Sizes**:
- **Small effects**: Detectable but may not be ecologically important
- **Large effects**: Both statistically significant and ecologically meaningful
- Consider both significance and magnitude

---

## Best Practices

### Data Preparation

**Quality Control**:
- Verify species names are consistent between datasets
- Check for missing or malformed coordinates
- Ensure date formats are correct (YYYYMMDD)
- Remove obvious data entry errors

**Sample Size Considerations**:
- **Minimum for network analysis**: 50+ species, 100+ plots
- **Temporal analysis**: At least 20 occurrences per time period per species
- **Dark diversity analysis**: Comprehensive regional species list essential

**Temporal Analysis**:
- Ensure adequate time separation between periods (minimum 5 years recommended)
- Balance sample sizes between time periods
- Consider seasonal effects in data collection

### Analysis Strategy

**Start Simple**:
1. Begin with broad taxonomic and habitat filters
2. Create initial network with common species
3. Add rare species and complexity gradually
4. Save intermediate results for comparison

**Iterative Approach**:
- Try different filter combinations
- Compare results across parameter settings
- Validate patterns with ecological knowledge
- Document decision rationale

**Statistical Considerations**:
- Use appropriate significance levels (0.05 for most applications)
- Consider multiple testing corrections for many comparisons
- Focus on both statistical significance and ecological relevance
- Report effect sizes alongside p-values

### Interpretation Guidelines

**Ecological Validation**:
- Compare results with known ecological patterns
- Consult field experience and literature
- Involve local ecological experts
- Consider landscape and management history

**Temporal Changes**:
- Distinguish between natural succession and anthropogenic change
- Consider external drivers (climate change, management changes)
- Evaluate spatial patterns of change
- Look for early warning indicators

**Dark Diversity Assessment**:
- Consider dispersal limitations for missing species
- Evaluate habitat suitability for potential species
- Prioritize restoration efforts based on feasibility
- Consider ecosystem service implications

---

## Troubleshooting

### Common Data Issues

**Import Problems**:
- **Error: Column not found**
  - *Solution*: Check that required columns exist in your data files
  - Ensure exact spelling and case sensitivity

- **Date parsing errors**
  - *Solution*: Ensure dates are in YYYYMMDD format
  - Remove any text or special characters from date columns

- **Memory issues with large datasets**
  - *Solution*: Use filtering to reduce dataset size
  - Consider using the stratified sampling option

**Network Analysis Issues**:
- **Too few species for network**
  - *Solution*: Reduce minimum occurrence threshold
  - Expand taxonomic or habitat filters
  - Consider using multiple habitat types

- **Layout not converging**
  - *Solution*: Increase iteration count
  - Try different random seeds
  - Check for isolated nodes in network

### Performance Optimization

**Speed Up Analysis**:
- Use cached data when possible
- Apply filters before network analysis
- Use subsampling for very large datasets
- Close unused browser tabs

**Memory Management**:
- Clear cache if disk space is limited
- Export intermediate results
- Work with filtered datasets rather than full data
- Restart application if memory usage is high

### Result Interpretation Issues

**Unexpected Patterns**:
- **Species in wrong positions**: May indicate data quality issues or real ecological surprises
- **No temporal changes detected**: May need longer time periods or different filtering
- **Very high/low dark diversity**: Check regional species pool completeness

**Statistical Issues**:
- **No significant results**: May need larger sample sizes or longer time periods
- **Everything is significant**: May indicate insufficient filtering or multiple testing issues

---

## Technical Details

### Algorithms Used

**Network Layout**:
- **Fruchterman-Reingold Algorithm**: Spring-embedding method that positions nodes to minimize edge crossings while maintaining edge length proportionality
- **Iterative optimization**: Repeatedly adjusts positions to improve layout quality
- **Deterministic with seed**: Same input data and seed always produce same layout

**Community Detection**:
- **Leiden Algorithm**: Optimizes modularity to find densely connected groups
- **Louvain Algorithm**: Alternative community detection method
- **Modularity**: Measures quality of community structure (higher = better separation)

**Statistical Testing**:
- **Bootstrap Resampling**: Randomly reassigns group memberships to test significance
- **Permutation Tests**: Compares observed changes to random expectation
- **Welch's T-test**: Compares means between groups with unequal variances

**Spatial Analysis**:
- **Kernel Density Estimation (KDE)**: Creates smooth density surfaces from point data
- **Clark-Evans R Statistic**: Measures spatial clustering vs. random expectation
- **Convex Hull**: Calculates minimum area containing all points

### Data Structures

**SQLite Databases**:
- **Efficient storage**: Compressed and indexed for fast access
- **ACID compliance**: Reliable data integrity
- **Cross-platform**: Works on all operating systems
- **Self-contained**: Single file contains entire database

**Parquet Caching**:
- **Columnar format**: Optimized for analytical workloads
- **Compression**: Significantly smaller file sizes
- **Fast loading**: Much faster than CSV for repeated access
- **Schema preservation**: Maintains data types accurately

### System Requirements

**Minimum Requirements**:
- Python 3.8+
- 4 GB RAM
- 1 GB free disk space
- Modern web browser

**Recommended**:
- Python 3.9+
- 8+ GB RAM  
- 5+ GB free disk space
- Chrome or Firefox browser

**Large Dataset Requirements**:
- 16+ GB RAM for >100,000 records
- SSD storage for optimal performance
- High-resolution monitor for detailed maps

### File Format Specifications

**NOVANA Data CSV Format**:
```
aktId,artId,almindeligtNavn,dato,naturtypeId,UTMx,UTMy,aarstal,...
12345,67890,"Almindelig Rødkløver",20230615,6510,551234,6234567,2023,...
```

**Taxa Excel Format**:
- Sheet name: "data"
- Required columns: artId, almindeligtNavn, videnskabeligtNavn, L, M, N, R, T
- Optional columns: Any additional trait or classification data

**Flora Danica CSV Format**:
```
species,decimalLongitude,decimalLatitude,eventDate,year,...
"Trifolium pratense",9.5678,55.1234,20230615,2023,...
```

### Integration with Other Tools

**Export Compatibility**:
- **R**: CSV and SQLite exports work directly with R packages
- **QGIS**: Geographic coordinates can be mapped in QGIS
- **Excel**: All tabular outputs compatible with Excel
- **Matplotlib/Seaborn**: Figure code can be adapted for custom plots

**API Considerations**:
- Currently designed as standalone application
- SQLite databases provide programmatic access to results
- Future versions may include REST API functionality

---

## Appendix: Ecological Background

### Ellenberg Indicator Values

**Light (L)**: 1 = deep shade, 9 = full sun
**Moisture (M)**: 1 = dry, 9 = aquatic  
**Nitrogen (N)**: 1 = very infertile, 9 = extremely fertile
**Reaction/pH (R)**: 1 = very acidic, 9 = very alkaline
**Temperature (T)**: 1 = cold, 9 = warm

### Network Ecology Principles

**Co-occurrence Networks**: Based on the principle that species found together share similar ecological requirements or interact ecologically.

**Small World Networks**: Ecological networks often show "small world" properties - most species are connected through short paths.

**Modularity**: Ecological communities often show modular structure with dense connections within modules and sparse connections between them.

### Conservation Applications

**Restoration Ecology**: Dark diversity analysis identifies specific species that could potentially be restored to degraded habitats.

**Monitoring**: Temporal analysis can detect early warning signs of ecosystem change before they become obvious in the field.

**Conservation Planning**: Species position in ecological space helps prioritize conservation efforts for specialized vs. generalist species.

---

**End of Manual**

*For technical support or questions about ecological interpretation, contact the development team through the GitHub repository or reach out to Flemming Skov at Aarhus University.*