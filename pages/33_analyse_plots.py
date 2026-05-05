"""
NOVANA Vegetation Analyzer - Plot Mapping Module
===============================================
This module visualizes vegetation plots in both ecological and geographic space.
It creates distribution maps of plots colored by habitat types or environmental
conditions, analyzes temporal changes in plot positions, and generates geographic
maps with UTM coordinates. The module includes density analysis, spatial pattern
detection, and environmental gradient visualization at the plot level.

Part of the NOVANA Vegetation Analyzer toolkit (mapping 2/2)
Author: Flemming Skov (flemming.skov@ecos.au.dk)
Last Updated: July 2025
"""

# Import packages for web applications
import streamlit as st

# Import packages for data manipulation and analysis
import pandas as pd
import numpy as np
import sqlite3

# Import packages for file and system operations
from pathlib import Path
from matplotlib.path import Path as MplPath 
import datetime
import warnings

# Import packages for type hints
from typing import Optional, Tuple, List, Dict

# Import packages for visualization
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
import matplotlib.cm as cm
from matplotlib.colors import ListedColormap

# Import packages for GIS functionality
import contextily as ctx
ctx.set_cache_dir("./map_cache")  # Creates local cache folder

# Suppress warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
#warnings.filterwarnings('ignore', message='.*Arrow.*')

# Page configuration
st.set_page_config(
    page_title="Mapping Survey plots", 
    page_icon="🗺️",
    layout="wide"
)

# Custom CSS for consistent styling
st.markdown("""
<style>
    .stTextInput > label {
        font-weight: bold;
        color: #2c3e50;
    }
    .info-box {
        background-color: #e8f4f8;
        border: 1px solid #b8e0ea;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    div[data-testid="stExpander"] > details {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Title and progress indicator
col1, col2 = st.columns([4, 1])
with col1:
    st.header("Maps")
    st.subheader("🌿 Habitat maps")
    st.markdown("*Mapping habitat distribution in ecological and geographic space and Ellemberg profiles*")
with col2:
    pass
st.markdown("---")


###################################################################################
# FUNCTIONS
###################################################################################

@st.cache_data(show_spinner=False)
def load_map_data(db_path: str) -> Dict[str, pd.DataFrame]:
    """Load all relevant tables from map database"""
    try:
        conn = sqlite3.connect(db_path)
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
        
        data_dict = {}
        for table in tables['name'].values:
            if not table.startswith('_'):  # Skip metadata tables
                data_dict[table] = pd.read_sql_query(f'SELECT * FROM {table}', conn)
        
        conn.close()
        return data_dict
    except Exception as e:
        st.error(f"Error loading map data: {str(e)}")
        return {}

def create_base_map(title: str = '', figsize: Tuple[int, int] = (12, 12)) -> Tuple[plt.Figure, plt.Axes]:
    """Create a base map with guide circles and lines"""
    fig, ax = plt.subplots(figsize=figsize)
    
    # Set up the plot
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_aspect('equal')
    
    # Draw guide circles
    center = (0.5, 0.5)
    radii = [0.125, 0.25, 0.375, 0.5]
    for radius in radii:
        circle = Circle(center, radius, linewidth=0.5, color='gray', fill=False, alpha=0.3)
        ax.add_patch(circle)
    
    # Draw guide lines
    ax.add_line(Line2D([0.5, 0.5], [0, 1], color='gray', linewidth=0.5, alpha=0.3))
    ax.add_line(Line2D([0, 1], [0.5, 0.5], color='gray', linewidth=0.5, alpha=0.3))
    ax.add_line(Line2D([0, 1], [0, 1], color='gray', linewidth=0.5, alpha=0.3))
    ax.add_line(Line2D([0, 1], [1, 0], color='gray', linewidth=0.5, alpha=0.3))
    
    # Labels and title
    ax.set_xlabel('X coordinate', fontsize=10, alpha=0.7)
    ax.set_ylabel('Y coordinate', fontsize=10, alpha=0.7)
    ax.set_title(title, fontsize=16, pad=20)
    ax.grid(False)
    
    return fig, ax

def get_color_palette(n_colors: int, palette_name: str = 'viridis') -> List:
    """Get a color palette with the specified number of colors"""
    if n_colors <= 20:
        return sns.color_palette(palette_name, n_colors)
    else:
        return sns.color_palette('husl', n_colors)

def save_figure(fig: plt.Figure, filename: str, figures_path: Path) -> bool:
    """Save figure to file"""
    try:
        if not figures_path.exists():
            figures_path.mkdir(parents=True, exist_ok=True)
        
        filepath = figures_path / f"{filename}.png"
        fig.savefig(filepath, dpi=500   , bbox_inches='tight', pad_inches=0.1)
        return True
    except Exception as e:
        st.error(f"Error saving figure: {str(e)}")
        return False

#### TEST AREA

from scipy.stats import gaussian_kde
import numpy as np

def draw_ecological_contour(ax, subset_df, label, color,
                             percentile=20, alpha=0.4,
                             label_alpha=0.6, rotation=0,
                             repel_from=None, linewidth=1.8, linestyle='dashed'):
    """
    Draw an outer KDE contour around plots meeting an ecological condition.
    
    Parameters:
    -----------
    repel_from : tuple (x, y) or None
        If provided, the label is placed at the contour boundary point 
        furthest from this coordinate — useful to separate overlapping labels.
    """
    if len(subset_df) < 15:
        return
    
    x = subset_df['xcoor'].values
    y = subset_df['ycoor'].values
    
    kde = gaussian_kde(np.vstack([x, y]), bw_method=0.25)
    
    xi = np.linspace(0, 1, 150)
    yi = np.linspace(0, 1, 150)
    Xi, Yi = np.meshgrid(xi, yi)
    Zi = kde(np.vstack([Xi.ravel(), Yi.ravel()])).reshape(Xi.shape)
    
    point_densities = kde(np.vstack([x, y]))
    threshold = np.percentile(point_densities, percentile)
    
    cs = ax.contour(Xi, Yi, Zi, levels=[threshold],
                    colors=[color], alpha=alpha, linewidths=linewidth,
                    linestyles=linestyle)
    
    # Label placement: furthest contour point from repel_from, 
    # or centroid fallback
    label_x, label_y = x.mean(), y.mean()  # default fallback
    
    if repel_from is not None:
        paths = cs.get_paths()
        if paths:
            all_verts = np.concatenate([p.vertices for p in paths], axis=0)
            dists = np.sqrt((all_verts[:, 0] - repel_from[0])**2 + 
                            (all_verts[:, 1] - repel_from[1])**2)
            furthest = all_verts[np.argmax(dists)]
            label_x, label_y = furthest
    else:
        # Centroid of the contour region
        mask = Zi >= threshold
        if mask.any():
            label_x = Xi[mask].mean()
            label_y = Yi[mask].mean()
    
    ax.text(label_x, label_y, label,
            fontsize=10, color=color, fontweight='bold',
            ha='center', va='center', alpha=label_alpha,
            rotation=rotation,
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                      alpha=0.4, edgecolor='none'))


def create_annotated_background(ax: plt.Axes, plot_df: pd.DataFrame, text_alpha: float = 0.1, line_alpha: float = 0.2, nr_percentile: float = 15, l_percentile: float = 12.5, salt_distance: float = 65) -> None:
    """
    Render a multi-layer ecological backdrop onto an existing matplotlib axes object.

    The background consists of five stacked layers, drawn in order from bottom to top:
      1. Moisture zones      — hexbin cells shaded by Ellenberg M (dry / mesic / wet)
      2. Low-light overlay   — dark green hexbin borders for low Ellenberg L plots,
                               fading outward from the distribution centroid
      3. Halophytic overlay  — steel blue hexbin borders for nature type 1330,
                               intensity scaled by local plot density
      4. Ecological contours — KDE contours marking nutrient-poor (N) and low-pH (R) zones
      5. Text labels         — 'Shade - Forest', 'Salty', 'Wet', 'Dry' placed at distribution centres

    Parameters:
    -----------
    ax : plt.Axes
        The matplotlib axes to draw on. Must already have xlim/ylim set to [0, 1].
    plot_df : pd.DataFrame
        Full (unfiltered) plot data. Required columns: xcoor, ycoor, M.
        Optional columns used when present: N, R, L, naturtypeId.
    text_alpha : float
        Opacity for all text labels and contour label boxes (default 0.1).
        Exposed as a Streamlit slider so the user can dim all text together.
    line_alpha : float
        Opacity for KDE contour lines and hexagon overlay borders (default 0.2).
        Exposed as a Streamlit slider so the user can dim all overlays together.
    nr_percentile : float
        Percentile threshold for defining nutrient-poor (N) and low-pH (R) zones (default 15).
        Lower values = more extreme/rare conditions only. Exposed as a Streamlit slider.
    l_percentile : float
        Percentile threshold for defining low-light (shade/forest) zones (default 12.5).
        Lower values = darker/more extreme shade only. Exposed as a Streamlit slider.
    salt_distance : float
        Percentile distance cutoff for halophytic zone display (default 65).
        Controls how far from core the salt zone extends. Higher = tighter boundaries.
    """

    # -------------------------------------------------------------------------
    # SETUP & VALIDATION
    # -------------------------------------------------------------------------

    # Minimum columns needed to proceed
    required_cols = ['xcoor', 'ycoor', 'M']
    if not all(col in plot_df.columns for col in required_cols):
        st.warning("Missing required columns for annotated background (xcoor, ycoor, M)")
        return

    # Drop rows with missing coordinates or moisture values
    valid_data = plot_df.dropna(subset=['xcoor', 'ycoor', 'M'])
    if len(valid_data) == 0:
        st.warning("No valid data for annotated background")
        return

    # Shared hexbin parameters
    GRIDSIZE    = 20                    # Hexagon grid resolution
    EXTENT      = (0.0, 1.0, 0.0, 1.0) # Match the ecological space coordinate range
    MINCNT      = 4                     # Minimum plots per hex cell for wet/dry overdraws
    MINCNT_RARE = 1                     # Lower threshold for rare/sparse distributions

    # RGBA fill colours for moisture zones (subtle pastels)
    moisture_colors = {
        'wet':   (0.78, 0.87, 0.93, 1.0),  # Blue tint
        'mesic': (0.91, 0.94, 0.97, 1.0),  # Near-neutral blue-grey
        'dry':   (0.97, 0.94, 0.89, 1.0),  # Warm beige
    }

    # -------------------------------------------------------------------------
    # THRESHOLDS
    # -------------------------------------------------------------------------

    # Moisture (M): bottom 10% = dry, middle 80% = mesic, top 10% = wet
    M_low  = np.percentile(valid_data['M'].dropna(), 10)
    M_high = np.percentile(valid_data['M'].dropna(), 90)

    # -------------------------------------------------------------------------
    # LAYER 1: MOISTURE BACKGROUND ZONES
    # A full mesic base layer is drawn first with mincnt=1 so that every hex
    # cell containing at least one plot is coloured — this eliminates white
    # cells entirely. Wet and dry zones are then overdrawn on top using the
    # stricter MINCNT threshold so only well-sampled cells change colour.
    # vmin=0.5 ensures zero-count cells fall below the colour range and are
    # rendered transparent rather than white via set_under/set_bad.
    # -------------------------------------------------------------------------

    wet_df  = valid_data[valid_data['M'] > M_high]
    dry_df  = valid_data[valid_data['M'] < M_low]

    # Base layer: ALL valid plots in mesic colour, mincnt=1 to leave no gaps
    cmap_base = ListedColormap([moisture_colors['mesic']])
    cmap_base.set_bad(color=(0, 0, 0, 0))
    cmap_base.set_under(color=(0, 0, 0, 0))
    ax.hexbin(
        valid_data['xcoor'], valid_data['ycoor'],
        gridsize=GRIDSIZE, extent=EXTENT, mincnt=1,
        cmap=cmap_base, vmin=0.5,
        edgecolors='lightgrey', alpha=1.0, linewidth=0.2
    )

    # Overdraw wet and dry zones on top of the mesic base
    for subset, key in [(wet_df, 'wet'), (dry_df, 'dry')]:
        if len(subset) > 0:
            cmap = ListedColormap([moisture_colors[key]])
            cmap.set_bad(color=(0, 0, 0, 0))
            cmap.set_under(color=(0, 0, 0, 0))
            ax.hexbin(
                subset['xcoor'], subset['ycoor'],
                gridsize=GRIDSIZE, extent=EXTENT, mincnt=MINCNT,
                cmap=cmap, vmin=0.5,
                edgecolors='lightgrey', alpha=1.0, linewidth=0.2
            )

    # -------------------------------------------------------------------------
    # LAYER 2: LOW-LIGHT OVERLAY (Ellenberg L)
    # Hexagons occupied by low-L plots get a dark green border. The border
    # alpha and linewidth both decrease with distance from the distribution
    # centroid, creating a vignette effect — denser core = stronger signal.
    # Fill is transparent so the moisture colours beneath remain visible.
    # The per-hexagon alphas are scaled by line_alpha so the overlay slider
    # dims these borders together with the contours.
    # -------------------------------------------------------------------------

    if 'L' in valid_data.columns:
        # Select the lowest N% of L values to define the low-light zone (user-configurable)
        threshold_L = np.percentile(valid_data['L'].dropna(), l_percentile)
        low_L = valid_data[valid_data['L'] <= threshold_L]
        centroid_L = (low_L['xcoor'].mean(), low_L['ycoor'].mean())

        if len(low_L) > 0:
            hb_light = ax.hexbin(
                low_L['xcoor'], low_L['ycoor'],
                gridsize=GRIDSIZE, extent=EXTENT, mincnt=MINCNT_RARE,
                linewidth=1.2
            )
            hb_light.set_facecolor('none')

            # Compute normalised distance of each hex centre from the centroid
            offsets   = hb_light.get_offsets()
            cx, cy    = centroid_L
            distances = np.sqrt((offsets[:, 0] - cx)**2 + (offsets[:, 1] - cy)**2)
            norm_dist = distances / distances.max()

            # Alpha fades outward, then scaled globally by line_alpha slider
            alphas     = (0.5 - 0.4 * norm_dist) * line_alpha / 0.75
            linewidths = 2.5 - 1.7 * norm_dist                        # 2.5 → 0.8

            # Build per-hexagon RGBA edge colours (darkgreen = 0.0, 0.392, 0.0)
            r, g, b = 0.0, 0.392, 0.0
            edge_colors = np.column_stack([
                np.full(len(alphas), r),
                np.full(len(alphas), g),
                np.full(len(alphas), b),
                np.clip(alphas, 0.0, 1.0)
            ])
            hb_light.set_edgecolors(edge_colors)
            hb_light.set_linewidths(linewidths)

    # -------------------------------------------------------------------------
    # LAYER 3: HALOPHYTIC VEGETATION OVERLAY (nature type 1330)
    # Steel blue borders mark hexagons containing salt-tolerant coastal plots.
    # Border intensity scales with local plot density (from hexbin counts)
    # rather than distance, so denser clusters read as more prominent.
    # The per-hexagon alphas are scaled by line_alpha so the overlay slider
    # dims these borders together with the contours.
    # -------------------------------------------------------------------------

    if 'naturtypeId' in valid_data.columns:
        # naturtypeId may be stored as int or string depending on the database
        halo_df = valid_data[
            (valid_data['naturtypeId'] == 1330) |
            (valid_data['naturtypeId'] == '1330')
        ]

        if len(halo_df) > 0:
            centroid_halo = (halo_df['xcoor'].mean(), halo_df['ycoor'].mean())

            hb_halo = ax.hexbin(
                halo_df['xcoor'], halo_df['ycoor'],
                gridsize=GRIDSIZE, extent=EXTENT, mincnt=MINCNT_RARE,
                linewidth=1.2
            )
            hb_halo.set_facecolor('none')

            # Compute distance of each hex centre from the distribution centroid
            offsets   = hb_halo.get_offsets()
            cx, cy    = centroid_halo
            distances = np.sqrt((offsets[:, 0] - cx)**2 + (offsets[:, 1] - cy)**2)

            # Only keep hexagons within the core N% of the distribution (user-configurable)
            dist_threshold = np.percentile(distances, salt_distance)
            core_mask = distances <= dist_threshold

            # Normalise counts to [0, 1] for scaling alpha and linewidth
            counts      = hb_halo.get_array()
            norm_counts = counts / counts.max()

            # Dense hexagons get strong borders, scaled globally by line_alpha slider
            # Outer hexagons (beyond 75th percentile) are made fully transparent
            alphas     = (0.15 + 0.75 * norm_counts) * line_alpha / 0.8
            alphas     = np.where(core_mask, alphas, 0.0)
            linewidths = np.where(core_mask, 0.8 + 1.7 * norm_counts, 0.0)

            # Steel blue RGB (0.27, 0.51, 0.71) — coastal / saline feel
            r, g, b = 0.27, 0.51, 0.71
            edge_colors = np.column_stack([
                np.full(len(alphas), r),
                np.full(len(alphas), g),
                np.full(len(alphas), b),
                np.clip(alphas, 0.0, 1.0)
            ])
            hb_halo.set_edgecolors(edge_colors)
            hb_halo.set_linewidths(linewidths)    

    # -------------------------------------------------------------------------
    # LAYER 4: ECOLOGICAL GRADIENT CONTOURS (N and R)
    # KDE contours outline areas dominated by nutrient-poor and low-pH plots.
    # Label positions are repelled away from the opposite corner of the map
    # to guarantee separation. Both line opacity (line_alpha) and label opacity
    # (text_alpha) are controlled by the Streamlit sliders.
    # -------------------------------------------------------------------------

    if all(col in valid_data.columns for col in ['N', 'R']):
        # Select the lowest N% of N and R values (user-configurable)
        threshold_N = np.percentile(valid_data['N'].dropna(), nr_percentile)
        threshold_R = np.percentile(valid_data['R'].dropna(), nr_percentile)

        low_N = valid_data[valid_data['N'] <= threshold_N]
        low_R = valid_data[valid_data['R'] <= threshold_R]

        # Nutrient-poor: solid brown contour, label pushed toward top-left
        draw_ecological_contour(ax, low_N,
            label='Nutrient\npoor', color='saddlebrown',
            percentile=40, alpha=line_alpha, label_alpha=text_alpha,
            rotation=0, repel_from=(1.0, 0.0), linewidth=3.5, linestyle='solid')

        # Low pH: dashed dark blue contour, label pushed toward bottom-right
        draw_ecological_contour(ax, low_R,
            label='Low pH', color='darkblue',
            percentile=40, alpha=line_alpha, label_alpha=text_alpha,
            rotation=0, repel_from=(0.0, 1.0))

    # -------------------------------------------------------------------------
    # LAYER 5: TEXT LABELS
    # Simple text placed at the median/centroid of ecologically extreme plots.
    # All labels are black for a clean, consistent look.
    # All labels share text_alpha so they can be dimmed together.
    # -------------------------------------------------------------------------

    # Shade - Forest — placed at the centroid of the low-L distribution
    if 'L' in valid_data.columns and 'centroid_L' in dir():
        ax.text(
            centroid_L[0], centroid_L[1], 'Shade',
            fontsize=12, color='black', fontweight='bold',
            ha='center', va='center', alpha=text_alpha
        )

    # Salty — placed at the centroid of the halophytic (1330) distribution
    if 'naturtypeId' in valid_data.columns and 'centroid_halo' in dir():
        ax.text(
            centroid_halo[0], centroid_halo[1], 'Salty',
            fontsize=12, color='black', fontweight='bold',
            ha='center', va='center', alpha=text_alpha
        )

    # Wet — placed at the median position of very wet plots (M > 8)
    high_M = valid_data[valid_data['M'] > 8]
    if len(high_M) > 10:
        cx, cy = high_M['xcoor'].median(), high_M['ycoor'].median()
        ax.text(cx, cy, 'Wet',
                fontsize=12, color='black', fontweight='bold',
                ha='center', va='center', alpha=text_alpha)

    # Dry — placed at the median position of very dry plots (M < 3.5)
    low_M = valid_data[valid_data['M'] < 3.5]
    if len(low_M) > 10:
        cx, cy = low_M['xcoor'].median(), low_M['ycoor'].median()
        ax.text(cx, cy, 'Dry',
                fontsize=12, color='black', fontweight='bold',
                ha='center', va='center', alpha=text_alpha)


###################################################################################
# Main interface
###################################################################################

# Database selection
st.markdown("### 📁 Select Map Database")

overlay_path = Path(st.session_state.get('overlay_map_path', '.'))
if not overlay_path.exists():
    st.error(f"Overlay map directory not found: {overlay_path}")
    st.stop()

db_files = sorted([f.name for f in overlay_path.glob("*.db")])

if not db_files:
    st.error("No map databases found.")
    st.info("Please complete Step 6 (Prepare Map) first.")
    st.stop()

col1, col2 = st.columns([3, 1])

with col1:
    selected_db = st.selectbox(
        "Select map database:",
        options=db_files,
        help="Choose a prepared map database"
    )
    db_path = overlay_path / selected_db

with col2:
    if st.button("📊 Load Map Data", type="primary", use_container_width=True):
        map_data = load_map_data(str(db_path))
        if map_data:
            st.session_state.plot_map_data = map_data
            st.success(f"✅ Loaded {len(map_data)} tables")

# Show data info
if 'plot_map_data' in st.session_state:
    map_data = st.session_state.plot_map_data
    
    # Check for required table
    if 'aktId' not in map_data:
        st.error("Plot data (aktId table) not found in database")
        st.stop()
    
    plot_df = map_data['aktId']
    
    # Display summary statistics
    with st.expander("📊 Plot Data Summary", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Plots", f"{plot_df['aktId'].nunique():,}")
        with col2:
            if 'naturtypeId' in plot_df.columns:
                st.metric("Habitat Types", f"{plot_df['naturtypeId'].nunique():,}")
            else:
                st.metric("Habitat Types", "N/A")
        with col3:
            if 'major_type' in plot_df.columns:
                st.metric("Major Types", f"{plot_df['major_type'].nunique():,}")
            else:
                st.metric("Major Types", "N/A")
        with col4:
            if 'speciesNum' in plot_df.columns:
                st.metric("Avg Species/Plot", f"{plot_df['speciesNum'].mean():.1f}")
            else:
                st.metric("Avg Species/Plot", "N/A")
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📍 Plot Distribution",
        "📊 Temporal Changes", 
        "🌡️ Environmental Analysis",
        "🗺️ Habitat Overview"  # Add this
    ])    
        
    
    with tab1:
        st.markdown("### 📍 Plot Distribution Analysis")
        
        # Filtering options
        st.markdown("#### 🔍 Filter Plots")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Region filters
            if 'novanareg' in plot_df.columns:
                regions = plot_df['novanareg'].dropna().unique()
                selected_regions = st.multiselect(
                    "Select monitoring regions:",
                    options=sorted(regions),
                    default=list(regions)
                )
                filtered_plots = plot_df[plot_df['novanareg'].isin(selected_regions)] if selected_regions else plot_df
            else:
                filtered_plots = plot_df
            
            # Bioregion filter
            if 'bioreg' in filtered_plots.columns:
                bioregions = filtered_plots['bioreg'].dropna().unique()
                selected_bioregions = st.multiselect(
                    "Select bioregions:",
                    options=sorted(bioregions),
                    default=list(bioregions)
                )
                if selected_bioregions:
                    filtered_plots = filtered_plots[filtered_plots['bioreg'].isin(selected_bioregions)]
        
        with col2:
            # Major type filter - default to ALL major types
            if 'major_type' in filtered_plots.columns:
                major_types = filtered_plots['major_type'].dropna().unique()
                selected_major_types = st.multiselect(
                    "Select major vegetation types:",
                    options=sorted(major_types),
                    default=list(major_types)  # Default to ALL major types
                )
                if selected_major_types:
                    filtered_plots = filtered_plots[filtered_plots['major_type'].isin(selected_major_types)]
            
            # Habitat type filter - filtered based on selected major types
            if 'naturtypeId' in filtered_plots.columns and 'major_type' in filtered_plots.columns:
                # Get habitat types that belong to selected major types
                if selected_major_types:
                    available_habitats = filtered_plots[
                        filtered_plots['major_type'].isin(selected_major_types)
                    ]['naturtypeId'].dropna().unique()
                else:
                    available_habitats = filtered_plots['naturtypeId'].dropna().unique()
                
                habitat_types = sorted(available_habitats)
                selected_habitats = st.multiselect(
                    "Select specific habitat types:",
                    options=habitat_types,
                    default=habitat_types  # Default to all available habitats
                )
                if selected_habitats:
                    filtered_plots = filtered_plots[filtered_plots['naturtypeId'].isin(selected_habitats)]
        
        st.info(f"Showing {len(filtered_plots)} plots after filtering")
        
        # Map settings
        st.markdown("#### 🎨 Map Settings")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Change from radio to checkboxes
            st.markdown("**Visualization layers:**")
            show_background = st.checkbox("Show background (all plots)", value=True)
            show_background_annotated = st.checkbox("Show background (annotated)", value=False)
            show_scatter = st.checkbox("Scatter plot", value=True)
            show_density_contours = st.checkbox("Density contours (50/90)", value=False)
            show_density_contours2 = st.checkbox("Density contours all", value=False)
            show_density_shading = st.checkbox("Density shading", value=False)

        with col2:
            if 'major_type' in filtered_plots.columns and 'naturtypeId' in filtered_plots.columns:
                legend_by = st.radio(
                    "Color/Legend by:",
                    options=["naturtypeId", "major_type"],
                    index=1
                )
            else:
                legend_by = None
            
            if 'speciesNum' in filtered_plots.columns:
                size_by_species = st.checkbox("Size by species count", value=True)
            else:
                size_by_species = False
            
            # Annotation transparency controls (only show if annotated background is enabled)
            if show_background_annotated:
                text_alpha = st.slider("Text transparency:", 0.0, 1.0, 0.7, 0.05, key="text_alpha1")
                line_alpha = st.slider("Overlay transparency:", 0.0, 1.0, 0.2, 0.05, key="line_alpha1")
                nr_percentile = st.slider("N/R threshold (%):", 5, 25, 15, 1, key="nr_percentile1",
                    help="Percentile for nutrient-poor/low-pH zones. Lower = more extreme conditions only.")
                l_percentile = st.slider("Light threshold (%):", 5.0, 25.0, 12.5, 0.5, key="l_percentile1",
                    help="Percentile for shade/forest zones. Lower = darker shade only.")
                salt_distance = st.slider("Salt zone extent (%):", 50, 90, 65, 5, key="salt_distance1",
                    help="Distance cutoff for halophytic zones. Higher = tighter boundaries around core.")

        with col3:
            zoom = st.slider("Zoom:", -0.1, 0.25, -0.05)

            # Scatter plot transparency control
            if show_scatter:
                scatter_alpha = st.slider("Scatter transparency:", 0.1, 1.0, 0.7, 0.05, key="scatter_alpha_tab1")
            else:
                scatter_alpha = 0.7  # Default value when scatter plot is not shown

            if show_density_contours or show_density_shading:
                kde_thresh = st.slider("Density threshold:", 0.01, 0.05, 0.005)
          
        st.markdown("#### 🎨 Map Settings")
         
        # Create the map
        fig, ax = create_base_map("Plot distribution")
        
        # Plot background layer first (all plots in light grey) if requested
        if show_background:
            ax.scatter(
                plot_df['xcoor'], plot_df['ycoor'],
                s=40, alpha=0.45, c='lightgrey',
                edgecolors='lightgrey', linewidths=0.05
            )
        
        
        # Add annotated background if requested (after basic background, before other layers)
        if show_background_annotated:
            create_annotated_background(ax, plot_df, text_alpha, line_alpha, nr_percentile, l_percentile, salt_distance)
        
        # Apply visualizations based on checkboxes
        if show_density_shading and len(filtered_plots) > 2:
            try:
                sns.kdeplot(
                    data=filtered_plots, x='xcoor', y='ycoor',
                    fill=True, cmap='Blues', levels=20,
                    thresh=kde_thresh, alpha=0.5, ax=ax
                )
            except:
                st.warning("Could not create density shading")
        
        if show_density_contours and len(filtered_plots) > 2:
            try:
                sns.kdeplot(
                    data=filtered_plots, x='xcoor', y='ycoor',
                    fill=False, levels=2,
                    thresh=0.1, alpha=1, color='blue', ax=ax
                )
                sns.kdeplot(
                    data=filtered_plots, x='xcoor', y='ycoor',
                    fill=False, levels=2,
                    thresh=0.5, alpha=1, color='red', ax=ax
                )
            except:
                st.warning("Could not create density contours")


        if show_density_contours2 and len(filtered_plots) > 2:
            try:
                sns.kdeplot(
                    data=filtered_plots, x='xcoor', y='ycoor',
                    fill=False, levels=24, linewidths=0.56,
                    thresh=0.05, alpha=0.8, color='black', ax=ax
                )
            except:
                st.warning("Could not create density contours")


      
        if show_scatter:
            # Determine sizes
            if size_by_species and 'speciesNum' in filtered_plots.columns:
                sizes = filtered_plots['speciesNum'] * 5
            else:
                sizes = 12
            
            # Plot by category if specified
            if legend_by and legend_by in filtered_plots.columns:
                unique_values = filtered_plots[legend_by].dropna().unique()
                colors = get_color_palette(len(unique_values))
                
                for i, value in enumerate(unique_values):
                    subset = filtered_plots[filtered_plots[legend_by] == value]
                    if size_by_species and 'speciesNum' in subset.columns:
                        subset_sizes = subset['speciesNum'] * 4
                    else:
                        subset_sizes = 12
                    
                    ax.scatter(
                        subset['xcoor'], subset['ycoor'],
                        s=subset_sizes, alpha=scatter_alpha, c=[colors[i]],
                        label=str(value)[:30], linewidths=0.5
                    )
                
                if len(unique_values) <= 20:
                    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
                             ncol=1 if len(unique_values) <= 10 else 2)
            else:
                ax.scatter(
                    filtered_plots['xcoor'], filtered_plots['ycoor'],
                    s=sizes, alpha=scatter_alpha, c='darkgreen',
                    edgecolors='black', linewidths=0.5
                )
        
        ax.set_xlim(zoom, 1 - zoom)
        ax.set_ylim(zoom, 1 - zoom)
        
        st.pyplot(fig)
        
        # Save option
        col1, col2 = st.columns([2, 1])
        with col1:
            save_name = st.text_input("Save as:", value="plot_distribution", key="save_plot1")
        with col2:
            if st.button("💾 Save Map", key="save_btn_plot1"):
                figures_path = Path(st.session_state.get('figures_path', '.'))
                if save_figure(fig, save_name, figures_path):
                    st.success(f"Map saved as {save_name}.png")
        
        plt.close()
        
        # Geographic map section
        st.markdown("---")
        st.markdown("### 🌍 Geographic Distribution")
        
        # Check if UTM coordinates are available
        if 'UTMx' in filtered_plots.columns and 'UTMy' in filtered_plots.columns:
            # Remove any plots with missing coordinates
            geo_plots = filtered_plots.dropna(subset=['UTMx', 'UTMy'])
            dk_dot_map = st.session_state.get('df_regional_pool', None)          
            
            if len(geo_plots) > 0:
                # Create geographic map
                fig_geo, ax_geo = plt.subplots(figsize=(12, 10))
                
                # Map settings for geographic view
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    geo_show_background = st.checkbox(
                        "Show geographic background", 
                        value=True,
                        key="geo_background",
                        help="Show all available geographic points as background"
                    )
                    
                    use_fixed_extent = st.checkbox(
                        "Fixed map extent (full extent)",
                        value=True,
                        key="fixed_extent",
                        help="Always show same area vs zoom to data"
                    )
                    
                    geo_color_by = st.selectbox(
                        "Color geographic points by:",
                        options=['major_type', 'naturtypeId', 'novanareg', 'bioreg', 'None'],
                        index=0,
                        key="geo_color"
                    )
                
                with col2:
                    geo_point_size = st.slider("Point size:", 5, 50, 15, key="geo_size")
                    
                with col3:
                    show_geo_density = st.checkbox("Show density overlay", value=False, key="geo_density")
                
                # Plot based on coloring choice
                if geo_color_by != 'None' and geo_color_by in geo_plots.columns:
                    unique_values = geo_plots[geo_color_by].dropna().unique()
                    colors = get_color_palette(len(unique_values))
                    
                    for i, value in enumerate(unique_values):
                        subset = geo_plots[geo_plots[geo_color_by] == value]
                        ax_geo.scatter(
                            subset['UTMx'], subset['UTMy'],
                            s=geo_point_size, alpha=0.7, c=[colors[i]],
                            label=str(value)[:30], edgecolors='black', linewidths=0.5
                        )
                    
                    if len(unique_values) <= 20:
                        ax_geo.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
                                     ncol=1 if len(unique_values) <= 10 else 2)
                else:
                    ax_geo.scatter(
                        geo_plots['UTMx'], geo_plots['UTMy'],
                        s=geo_point_size, alpha=0.7, c='darkgreen',
                        edgecolors='black', linewidths=0.5
                    )
                
                
                if use_fixed_extent:
                    ax_geo.set_xlim(425000, 910000)
                    ax_geo.set_ylim(6040000, 6415000)
                    
                
                if geo_show_background:
                    try:
                        ctx.add_basemap(
                            ax_geo,
                            crs="EPSG:25832",
                            source=ctx.providers.CartoDB.Positron,
                            zoom=9,
                            alpha=0.75,
                            attribution=False
                        )
                    except Exception as e:
                        st.warning(f"Could not load basemap: {e}")
                
                # Add density overlay if requested
                if show_geo_density and len(geo_plots) > 2:
                    try:                  
                        sns.kdeplot(
                            data=geo_plots, x='UTMx', y='UTMy',
                            fill=False, cmap='Reds', levels=12,
                            thresh=0.05, alpha=0.95, ax=ax_geo
                        )
                    except:
                        st.warning("Could not create density overlay")
                
                # Set labels and title
                ax_geo.set_xlabel('utm x', fontsize=12)
                ax_geo.set_ylabel('utm y', fontsize=12)
                ax_geo.set_title('Distribution of plots', fontsize=16, pad=20)
                ax_geo.grid(True, alpha=0.3)
                
                # Set aspect ratio to equal for proper geographic representation
                ax_geo.set_aspect('equal', adjustable='box')
                
                # Add plot count
                ax_geo.text(0.02, 0.98, f"Plots shown: {len(geo_plots)}",
                           transform=ax_geo.transAxes, verticalalignment='top', 
                           fontsize=12, bbox=dict(boxstyle="round,pad=0.3", 
                                                 facecolor="white", alpha=0.8))
                
                st.pyplot(fig_geo)
                
                # Save option for geographic map
                col1, col2 = st.columns([2, 1])
                with col1:
                    save_name_geo = st.text_input("Save as:", value="plot_geographic", key="save_geo")
                with col2:
                    if st.button("💾 Save Map", key="save_btn_geo"):
                        figures_path = Path(st.session_state.get('figures_path', '.'))
                        if save_figure(fig_geo, save_name_geo, figures_path):
                            st.success(f"Map saved as {save_name_geo}.png")
                
                plt.close()
                
                # Summary statistics for geographic distribution
                with st.expander("📊 Geographic Statistics"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("X Range (m)", f"{geo_plots['UTMx'].max() - geo_plots['UTMx'].min():,.0f}")
                        st.metric("Min X", f"{geo_plots['UTMx'].min():,.0f}")
                    with col2:
                        st.metric("Y Range (m)", f"{geo_plots['UTMy'].max() - geo_plots['UTMy'].min():,.0f}")
                        st.metric("Min Y", f"{geo_plots['UTMy'].min():,.0f}")
                    with col3:
                        st.metric("Coverage Area", f"~{((geo_plots['UTMx'].max() - geo_plots['UTMx'].min()) * (geo_plots['UTMy'].max() - geo_plots['UTMy'].min()) / 1e6):,.1f} km²")
                        st.metric("Max Y", f"{geo_plots['UTMy'].max():,.0f}")
            else:
                st.warning("No valid geographic coordinates found in filtered data")
        else:
            st.info("Geographic coordinates (UTMx, UTMy) not available in this dataset")
            

# Combined Geographic and Ecological Distribution Map
        st.markdown("---")
        st.markdown("### 🗺️ Combined Distribution View")

        # Combined map settings
        col1, col2, col3 = st.columns(3)

        with col1:
            show_combined_contours = st.selectbox(
                "Show KDE contours & hull:",
                options=["On", "Off"],
                index=0,  # Default to "On"
                key="combined_contours"
            ) == "On"

        with col2:
            show_combined_legend = st.selectbox(
                "Show legend box:",
                options=["On", "Off"], 
                index=0,  # Default to "On"
                key="combined_legend"
            ) == "On"

        with col3:
            # Default title based on current filter description
            default_title = f"{len(filtered_plots)} plots"
            if selected_habitats and 'naturtypeId' in filtered_plots.columns:
                unique_habitats = sorted(filtered_plots['naturtypeId'].dropna().unique())
                if len(unique_habitats) <= 5:
                    habitat_list = ', '.join(map(str, unique_habitats))
                else:
                    habitat_list = ', '.join(map(str, unique_habitats[:3])) + f' + {len(unique_habitats)-3} more'
                default_title = f"Habitat type(s): {habitat_list}"
            elif selected_major_types:
                default_title += f" - {', '.join(selected_major_types)}"
            
            combined_figure_title = st.text_input(
                "Figure title:",
                value=default_title,
                key="combined_title"
            )

        # Create new combined figure (A4 width)
        #fig_combined, (ax_geo_combined, ax_eco_combined) = plt.subplots(1, 2, figsize=(11.7, 6))
        
        fig_combined, (ax_geo_combined, ax_eco_combined) = plt.subplots(
                                                1, 2, 
                                                figsize=(11.7, 6),
                                                gridspec_kw={'width_ratios': [56.5, 43.5]}  # 60% left, 40% right
                                            )

        # Add border around entire figure
        for spine in fig_combined.patch.get_children():
            if hasattr(spine, 'set_linewidth'):
                spine.set_linewidth(0.8)

        # --- LEFT: GEOGRAPHIC PLOT ---
        # Background
        # if 'df_regional_pool' in st.session_state:
        #     dk_dot_map = st.session_state['df_regional_pool']
        #     if not dk_dot_map.empty and 'utm_easting' in dk_dot_map.columns and 'utm_northing' in dk_dot_map.columns:
        #         valid_background = dk_dot_map.dropna(subset=['utm_easting', 'utm_northing'])
        #         if len(valid_background) > 0:
        #             ax_geo_combined.scatter(
        #                 valid_background['utm_easting'], valid_background['utm_northing'],
        #                 s=20, alpha=0.20, c='lightgrey', edgecolors='none'
        #             )

        # Plot the filtered plots geographically
        if 'UTMx' in filtered_plots.columns and 'UTMy' in filtered_plots.columns:
            geo_data_combined = filtered_plots.dropna(subset=['UTMx', 'UTMy'])
            
            if len(geo_data_combined) > 0:
                # Color by the same variable as the main maps if specified
                if legend_by and legend_by in geo_data_combined.columns:
                    unique_values = geo_data_combined[legend_by].dropna().unique()
                    colors = get_color_palette(len(unique_values))
                    
                    for i, value in enumerate(unique_values):
                        subset = geo_data_combined[geo_data_combined[legend_by] == value]
                        if len(subset) > 0:
                            ax_geo_combined.scatter(
                                subset['UTMx'], subset['UTMy'],
                                s=25, alpha=0.75, c=[colors[i]], 
                                edgecolors='black', linewidths=0.1
                            )
                else:
                    ax_geo_combined.scatter(
                        geo_data_combined['UTMx'], geo_data_combined['UTMy'],
                        s=25, alpha=0.75, c='red', 
                        edgecolors='black', linewidths=0.1
                    )
                    
        if use_fixed_extent:
                    ax_geo_combined.set_xlim(425000, 910000)
                    ax_geo_combined.set_ylim(6040000, 6415000)
                    
        if geo_show_background:
            try:
                ctx.add_basemap(
                    ax_geo_combined,
                    crs="EPSG:25832",
                    source=ctx.providers.CartoDB.Positron,
                    zoom=9,
                    alpha=0.75,
                    attribution=False
                )
            except Exception as e:
                st.warning(f"Could not load basemap: {e}")

        ax_geo_combined.set_xlabel('utm x', fontsize=10)
        ax_geo_combined.set_ylabel('utm y', fontsize=10)
        ax_geo_combined.set_title('Geographic distribution', fontsize=11)
        ax_geo_combined.grid(True, alpha=0.3)
        ax_geo_combined.set_aspect('equal', adjustable='box')

        # Add legend to geographic map if coloring by categories and if enabled
        if show_combined_legend and legend_by and legend_by in geo_data_combined.columns and len(unique_values) <= 10:
            # Create legend entries
            legend_elements = []
            for i, value in enumerate(unique_values):
                legend_elements.append(
                    plt.Line2D([0], [0], marker='o', color='w', 
                            markerfacecolor=colors[i], markersize=8,
                            label=str(value)[:25])  # Truncate long labels
                )
            
            # Add legend in upper right corner
            ax_geo_combined.legend(handles=legend_elements, loc='upper right', 
                                framealpha=0.9, fontsize=8, 
                                title=legend_by.replace('_', ' ').title())

        # --- RIGHT: ECOLOGICAL PLOT ---
        # Background elements
        center = (0.5, 0.5)
        radii = [0.125, 0.25, 0.375, 0.5]
        for radius in radii:
            circle = Circle(center, radius, linewidth=0.5, color='gray', fill=False, alpha=0.3)
            ax_eco_combined.add_patch(circle)

        # Add guide lines
        ax_eco_combined.add_line(Line2D([0.5, 0.5], [0, 1], color='gray', linewidth=0.5, alpha=0.3))
        ax_eco_combined.add_line(Line2D([0, 1], [0.5, 0.5], color='gray', linewidth=0.5, alpha=0.3))
        ax_eco_combined.add_line(Line2D([0, 1], [0, 1], color='gray', linewidth=0.5, alpha=0.3))
        ax_eco_combined.add_line(Line2D([0, 1], [1, 0], color='gray', linewidth=0.5, alpha=0.3))

        # Add background context - all plots
        if len(plot_df) > 0:
            all_plots_valid = plot_df.dropna(subset=['xcoor', 'ycoor'])
            all_plots_valid = all_plots_valid[
                (all_plots_valid['xcoor'] >= 0) & (all_plots_valid['xcoor'] <= 1) &
                (all_plots_valid['ycoor'] >= 0) & (all_plots_valid['ycoor'] <= 1)
            ]
            
            if len(all_plots_valid) > 0:
                ax_eco_combined.scatter(
                    all_plots_valid['xcoor'], all_plots_valid['ycoor'],
                    alpha=0.15, s=20, color='lightgrey', zorder=1
                )

        # Plot filtered plots in ecological space (plotted first so contours appear on top)
        if len(filtered_plots) > 0:
            # Color by same variable as main maps
            if legend_by and legend_by in filtered_plots.columns:
                unique_values = filtered_plots[legend_by].dropna().unique()
                colors = get_color_palette(len(unique_values))
                
                for i, value in enumerate(unique_values):
                    subset = filtered_plots[filtered_plots[legend_by] == value]
                    if len(subset) > 0:
                        ax_eco_combined.scatter(
                            subset['xcoor'], subset['ycoor'],
                            alpha=0.7, s=20, c=[colors[i]], zorder=3
                        )
            else:
                ax_eco_combined.scatter(
                    filtered_plots['xcoor'], filtered_plots['ycoor'],
                    alpha=0.7, s=20, color='darkgreen', zorder=3
                )

        # Add centroid if enough data
        if len(filtered_plots) > 0:
            try:
                coords_centroid = filtered_plots[['xcoor', 'ycoor']].values
                centroid = np.mean(coords_centroid, axis=0)
                ax_eco_combined.scatter([centroid[0]], [centroid[1]],
                                    s=150, color='red', marker='*', 
                                    edgecolor='darkred', linewidth=2, zorder=8)
            except Exception as e:
                pass

        # Add KDE contours for filtered plots if enough data and if enabled (plotted after scatter to appear on top)
        if show_combined_contours and len(filtered_plots) >= 3:
            try:
                
                # Create evaluation grid
                x_grid = np.linspace(-0.1, 1.1, 60)
                y_grid = np.linspace(-0.1, 1.1, 60)
                xx, yy = np.meshgrid(x_grid, y_grid)
                
                # Calculate KDE for filtered plots
                from scipy.stats import gaussian_kde
                
                coords_combined = filtered_plots[['xcoor', 'ycoor']].values
                kde = gaussian_kde(coords_combined.T)
                positions = np.vstack([xx.ravel(), yy.ravel()])
                density = kde(positions).reshape(xx.shape)
                
                # Find 90% and 50% contour levels
                sorted_density = np.sort(density.ravel())[::-1]
                cumsum = np.cumsum(sorted_density)
                total = cumsum[-1]
                level_90 = sorted_density[np.where(cumsum >= 0.9 * total)[0][0]]
                level_50 = sorted_density[np.where(cumsum >= 0.5 * total)[0][0]]
                
                # Plot 90% KDE contour (on top of scatter points)
                ax_eco_combined.contour(xx, yy, density, levels=[level_90], 
                                    colors=['blue'], linewidths=2, linestyles='-', alpha=0.8, zorder=10)
                
                # Plot 50% KDE contour (on top of scatter points)
                ax_eco_combined.contour(xx, yy, density, levels=[level_50], 
                                    colors=['red'], linewidths=2.3, linestyles='-', alpha=0.99, zorder=10)
                
            except Exception as e:
                pass  # Skip if KDE fails

        # Add convex hull for filtered plots if enabled (plotted after scatter to appear on top)
        if show_combined_contours and len(filtered_plots) >= 3:
            try:
                from scipy.spatial import ConvexHull
                from matplotlib.patches import Polygon
                
                coords_hull = filtered_plots[['xcoor', 'ycoor']].values
                hull = ConvexHull(coords_hull)
                hull_points = coords_hull[hull.vertices]
                hull_polygon = Polygon(hull_points, fill=False, 
                                    edgecolor='blue', linewidth=1.5, 
                                    linestyle='--', alpha=0.5, zorder=11)
                ax_eco_combined.add_patch(hull_polygon)
            except Exception as e:
                pass  # Skip if hull fails

        # Center marker (highest zorder to always be on top)
        ax_eco_combined.scatter([0.5], [0.5], s=75, color='green', marker='+', linewidth=3, zorder=15)

        ax_eco_combined.set_xlim(-0.05, 1.05)
        ax_eco_combined.set_ylim(-0.05, 1.05)
        ax_eco_combined.set_xlabel('x', fontsize=10, alpha=0.7)
        ax_eco_combined.set_ylabel('y', fontsize=10, alpha=0.7)
        ax_eco_combined.set_title('Ecological distribution', fontsize=11)
        ax_eco_combined.grid(True, alpha=0.2)
        ax_eco_combined.set_aspect('equal')

        plt.tight_layout(rect=[0.02, 0.08, 0.98, 0.95])  # Leave space for border and title

        # Add custom title at bottom
        fig_combined.text(0.08, 0.02, combined_figure_title, fontsize=12, fontweight='bold', 
                        transform=fig_combined.transFigure, verticalalignment='bottom')

        st.pyplot(fig_combined)

        # Save option for combined figure
        col1, col2 = st.columns([3, 1])
        with col1:
            # Create filename based on filters
            filename_parts = ["plots_combined"]
            if selected_major_types and len(selected_major_types) <= 3:
                clean_types = [t.replace(' ', '_').replace('(', '').replace(')', '').replace(',', '') for t in selected_major_types]
                filename_parts.extend(clean_types)
            
            default_combined_name = "_".join(filename_parts)
            save_name_combined = st.text_input("Save combined figure as:", 
                                            value=default_combined_name, 
                                            key="save_plots_combined")
        with col2:
            if st.button("💾 Save Combined Figure", key="save_btn_plots_combined"):
                figures_path = Path(st.session_state.get('figures_path', '.'))
                if save_figure(fig_combined, save_name_combined, figures_path):
                    st.success(f"Combined figure saved as {save_name_combined}.png")

        plt.close(fig_combined)
        
    
    with tab2:
        
        #####################################################
        st.markdown("### 📊 Temporal Change Analysis")
        #####################################################
        
        if 'aarstal' not in plot_df.columns:
            st.warning("No temporal data (aarstal) available in the plot data")
        else:
            # Select habitat type for temporal analysis
            if 'naturtypeId' in plot_df.columns:
                habitat_list = sorted(plot_df['naturtypeId'].dropna().unique())
                selected_habitat = st.selectbox(
                    "Select habitat type for temporal analysis:",
                    options=habitat_list,
                    help="Choose a habitat type to analyze changes over time"
                )
                
                # Filter for selected habitat
                habitat_data = plot_df[plot_df['naturtypeId'] == selected_habitat]
                n_plots = len(habitat_data)
                
                if n_plots > 0:
                    st.info(f"Analyzing {n_plots} plots of habitat type {selected_habitat}")
                    
                    # Time range settings
                    min_year = int(habitat_data['aarstal'].min())
                    max_year = int(habitat_data['aarstal'].max())
                    
                    if min_year < max_year:
                        # Calculate median year to split data roughly in half
                        median_year = int(habitat_data['aarstal'].median())
                        
                        # Set default values for slider to split data roughly equally
                        default_min = median_year - 1
                        default_max = median_year
                        
                        year_range = st.slider(
                            "Select time periods for comparison:",
                            min_value=min_year,
                            max_value=max_year,
                            value=(default_min, default_max),
                            help="Adjust to compare early vs late periods. Default splits data roughly in half."
                        )
                        
                        kde_threshold = st.slider(
                            "KDE threshold:",
                            min_value=0.01,
                            max_value=0.5,
                            value=0.05,
                            step=0.01,
                            help="Lower values show tighter contours",
                            key="temporal_kde"
                        )
                        
                        # Split data by time
                        early_data = habitat_data[habitat_data['aarstal'] <= year_range[0]]
                        late_data = habitat_data[habitat_data['aarstal'] > year_range[1]]
                        
                        # Create temporal comparison map
                        fig, ax = create_base_map(f'Temporal Change: Habitat {selected_habitat}')

                        show_background_annotated = st.checkbox("Show background (annotated)", value=False, key='box tab2')

                        # Alpha sliders (only show if checkbox is enabled)
                        if show_background_annotated:
                            text_alpha = st.slider("Text transparency:", 0.0, 1.0, 0.7, 0.05, key='text tab2')
                            line_alpha = st.slider("Overlay transparency:", 0.0, 1.0, 0.2, 0.05, key='overlay tab2')
                            nr_percentile = st.slider("N/R threshold (%):", 5, 25, 15, 1, key="nr_percentile2",
                                help="Percentile for nutrient-poor/low-pH zones. Lower = more extreme conditions only.")
                            l_percentile = st.slider("Light threshold (%):", 5.0, 25.0, 12.5, 0.5, key="l_percentile2",
                                help="Percentile for shade/forest zones. Lower = darker shade only.")
                            salt_distance = st.slider("Salt zone extent (%):", 50, 90, 65, 5, key="salt_distance2",
                                help="Distance cutoff for halophytic zones. Higher = tighter boundaries around core.")

                        if show_background_annotated:
                            create_annotated_background(ax, plot_df, text_alpha, line_alpha, nr_percentile, l_percentile, salt_distance)
                        
                        # Plot early period points in blue
                        ax.scatter(
                            early_data['xcoor'], early_data['ycoor'],
                            s=30, alpha=0.6, c='blue',
                            label=f'Early (≤{year_range[0]}): n = {len(early_data)}',
                            edgecolors='black', linewidths=0.5
                        )
                        
                        # Plot late period points in red
                        ax.scatter(
                            late_data['xcoor'], late_data['ycoor'],
                            s=30, alpha=0.6, c='red',
                            label=f'Late (>{year_range[1]}): n = {len(late_data)}',
                            edgecolors='black', linewidths=0.5
                        )
                        
                        # Plot KDE contours
                        if len(early_data) > 2:
                            try:
                                sns.kdeplot(
                                    data=early_data, x='xcoor', y='ycoor',
                                    levels=2, fill=False, thresh=kde_threshold,
                                    alpha=1, linewidths=1.5, color='blue', ax=ax
                                )
                            except:
                                st.info("Not enough early period data for KDE")
                        
                        if len(late_data) > 2:
                            try:
                                sns.kdeplot(
                                    data=late_data, x='xcoor', y='ycoor',
                                    levels=2, fill=False, thresh=kde_threshold,
                                    alpha=1, linewidths=3, color='red', ax=ax
                                )
                            except:
                                st.info("Not enough late period data for KDE")
                        
                        # Add annotations
                        ax.text(0.02, 0.98, f"Total plots: {n_plots}",
                               transform=ax.transAxes, verticalalignment='top', fontsize=12)
                        
                        ax.legend(loc='upper right')
                        
                        zoom = st.slider("Zoom:", -0.1, 0.25, -0.05, key="temporal_zoom")
                        ax.set_xlim(zoom, 1 - zoom)
                        ax.set_ylim(zoom, 1 - zoom)
                        
                        st.pyplot(fig)
                        
                        # Save option
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            save_name = st.text_input("Save as:", 
                                                    value=f"temporal_change_{selected_habitat}", 
                                                    key="save_temporal")
                        with col2:
                            if st.button("💾 Save Map", key="save_btn_temporal"):
                                figures_path = Path(st.session_state.get('figures_path', '.'))
                                if save_figure(fig, save_name, figures_path):
                                    st.success(f"Map saved as {save_name}.png")
                        
                        plt.close()
                        
                        # Summary statistics
                        with st.expander("📊 Movement Statistics"):
                            if len(early_data) > 0 and len(late_data) > 0:
                                early_center_x = early_data['xcoor'].mean()
                                early_center_y = early_data['ycoor'].mean()
                                late_center_x = late_data['xcoor'].mean()
                                late_center_y = late_data['ycoor'].mean()
                                
                                # Calculate movement
                                movement_dist = np.sqrt((late_center_x - early_center_x)**2 + 
                                                      (late_center_y - early_center_y)**2)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Center shift", f"{movement_dist:.3f} units")
                                    st.metric("Early center X", f"{early_center_x:.3f}")
                                    st.metric("Early center Y", f"{early_center_y:.3f}")
                                with col2:
                                    angle = np.degrees(np.arctan2(late_center_y - early_center_y,
                                                                 late_center_x - early_center_x))
                                    st.metric("Direction", f"{angle:.1f}°")
                                    st.metric("Late center X", f"{late_center_x:.3f}")
                                    st.metric("Late center Y", f"{late_center_y:.3f}")
                    else:
                        st.warning("Not enough temporal variation for analysis")
                else:
                    st.warning(f"No plots found for habitat type {selected_habitat}")
            else:
                st.error("No habitat type information available for temporal analysis")
    
    with tab3:
        st.markdown("### 🌡️ Environmental Analysis")
        
        # Check for environmental data
        env_cols = [col for col in plot_df.columns if col in ['M', 'N', 'L', 'R', 'T']]
        
        if not env_cols:
            st.info("No environmental indicator data (Ellenberg values) found in plot data")
            
            st.markdown("""
                Environmental indicators expected:
                - M: Moisture indicator
                - N: Nitrogen indicator
                - L: Light indicator
                - R: pH (Reaction) indicator
                - T: Temperature indicator
                """)
            
        else:
            # First, filter by major type if available
            filtered_env_plots = plot_df.copy()
            
            if 'major_type' in plot_df.columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Major type filter
                    major_types = plot_df['major_type'].dropna().unique()
                    
                    # Add "All types" option
                    major_type_options = ['All types'] + sorted(major_types.tolist())
                    
                    selected_major_type = st.selectbox(
                        "Select major vegetation type:",
                        options=major_type_options,
                        help="Filter data by major vegetation type or select 'All types' for complete dataset"
                    )
                    
                    # Apply major type filter
                    if selected_major_type != 'All types':
                        filtered_env_plots = filtered_env_plots[filtered_env_plots['major_type'] == selected_major_type]
                        st.info(f"Analyzing {len(filtered_env_plots)} plots of type: {selected_major_type}")
                    else:
                        st.info(f"Analyzing all {len(filtered_env_plots)} plots")
                
                with col2:
                    # Select environmental variable                    
                    env_labels = {
                        'M': 'Moisture',
                        'N': 'Nitrogen', 
                        'L': 'Light',
                        'R': 'pH (Reaction)',
                        'T': 'Temperature'
                    }
                    
                    selected_env = st.selectbox(
                        "Select environmental indicator:",
                        options=env_cols,
                        format_func=lambda x: env_labels.get(x, x)
                    )
            else:
                # No major type column, just show env selector
                env_labels = {
                    'L': 'Light',
                    'M': 'Moisture',
                    'R': 'pH (Reaction)',
                    'N': 'Nitrogen',
                    'T': 'Temperature'
                }
                
                selected_env = st.selectbox(
                    "Select environmental indicator:",
                    options=env_cols,
                    format_func=lambda x: env_labels.get(x, x)
                )
            
            # Filter out NaN values for selected environmental indicator
            env_data = filtered_env_plots.dropna(subset=[selected_env])
            
            if len(env_data) > 0:
                # Show distribution
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig_hist, ax_hist = plt.subplots(figsize=(8, 4))
                    ax_hist.hist(env_data[selected_env], bins=30, edgecolor='black', alpha=0.7)
                    ax_hist.set_xlabel(f"{env_labels.get(selected_env, selected_env)} Value")
                    ax_hist.set_ylabel("Number of Plots")
                    ax_hist.set_title(f"Distribution of {env_labels.get(selected_env, selected_env)} Values")
                    st.pyplot(fig_hist)
                    plt.close()
                
                with col2:
                    st.metric("Mean", f"{env_data[selected_env].mean():.2f}")
                    st.metric("Std Dev", f"{env_data[selected_env].std():.2f}")
                    st.metric("Range", f"{env_data[selected_env].min():.2f} - {env_data[selected_env].max():.2f}")
                
                # Create environmental gradient map
                fig, ax = create_base_map(f"{env_labels.get(selected_env, selected_env)} gradient")
                
                # Add value range slider
                env_min = float(env_data[selected_env].min())
                env_max = float(env_data[selected_env].max())
                
                value_range = st.slider(
                    f"Filter {env_labels.get(selected_env, selected_env)} value range:",
                    min_value=env_min,
                    max_value=env_max,
                    value=(env_min, env_max),
                    step=0.1,
                    help="Adjust to show only plots within this range"
                )
                
                # Filter data based on value range
                filtered_env_data = env_data[
                    (env_data[selected_env] >= value_range[0]) & 
                    (env_data[selected_env] <= value_range[1])
                ]
                
                st.info(f"Showing {len(filtered_env_data)} plots with {env_labels.get(selected_env, selected_env)} values between {value_range[0]:.1f} and {value_range[1]:.1f}")
                
                # Checkbox for showing scatter plot
                show_scatter_env = st.checkbox("Show scatter plot", value=True, key="env_scatter")
                
                # Scatter plot colored by environmental value
                if show_scatter_env:
                    scatter = ax.scatter(
                        filtered_env_data['xcoor'], filtered_env_data['ycoor'],
                        c=filtered_env_data[selected_env], cmap='RdYlBu_r',
                        s=50, alpha=0.8, edgecolors='black', linewidths=0.5
                    )
                    
                    # Add colorbar
                    cbar = plt.colorbar(scatter, ax=ax, shrink=0.75)
                    cbar.set_label(f"{env_labels.get(selected_env, selected_env)} Value", 
                                  rotation=270, labelpad=20)
            
                if st.checkbox("Show environmental gradient", value=False, key="env_gradient"):
                    try:
                        from scipy.interpolate import griddata
                        from scipy.ndimage import gaussian_filter
                        from scipy.spatial import ConvexHull
                        import numpy as np
                        
                        # Create finer grid for better edge coverage
                        xi = np.linspace(0, 1, 150)  # Increased resolution
                        yi = np.linspace(0, 1, 150)
                        xi, yi = np.meshgrid(xi, yi)
                        
                        # Get plot coordinates and values
                        points = filtered_env_data[['xcoor', 'ycoor']].values
                        values = filtered_env_data[selected_env].values
                        
                        # Create convex hull
                        hull = ConvexHull(points)
                        hull_path = MplPath(points[hull.vertices])
                        
                        # Use nearest neighbor interpolation to extend values closer to edges
                        zi = griddata(points, values, (xi, yi), method='nearest', fill_value=np.nan)
                        
                        # Apply lighter smoothing to preserve edge detail
                        zi_smooth = gaussian_filter(zi, sigma=0.95)
                        
                        # Mask values outside convex hull
                        grid_points = np.column_stack((xi.ravel(), yi.ravel()))
                        inside_hull = hull_path.contains_points(grid_points)
                        mask = inside_hull.reshape(xi.shape)
                        
                        # Apply mask - set outside points to NaN
                        zi_smooth[~mask] = np.nan
                        
                        # Create contour plot
                        levels = np.linspace(env_min, env_max, 12)
                        contour = ax.contourf(xi, yi, zi_smooth, levels=levels, cmap='RdYlBu_r', alpha=0.6)
                        
                        # Add contour lines
                        contour_lines = ax.contour(xi, yi, zi_smooth, levels=levels[::3], 
                                                colors='gray', alpha=0.5, linewidths=0.8)
                        
                        # Optionally add labels to contour lines
                        ax.clabel(contour_lines, inline=True, fontsize=8, fmt='%.1f')
                        
                        # Add colorbar if scatter is not shown
                        if not show_scatter_env:
                            cbar = plt.colorbar(contour, ax=ax, shrink=0.75)
                            cbar.set_label(f"{env_labels.get(selected_env, selected_env)} Value", 
                                        rotation=270, labelpad=20)                            
                        
                    except Exception as e:
                        st.warning(f"Could not create environmental gradient: {str(e)}")

                zoom = st.slider("Zoom:", -0.1, 0.25, -0.05, key="env_zoom")
                ax.set_xlim(zoom, 1 - zoom)
                ax.set_ylim(zoom, 1 - zoom)
                
                st.pyplot(fig)
                
                # Save option
                col1, col2 = st.columns([2, 1])
                with col1:
                    save_name = st.text_input("Save as:", 
                                            value=f"{selected_env}_gradient", 
                                            key="save_env")
                with col2:
                    if st.button("💾 Save Map", key="save_btn_env"):
                        figures_path = Path(st.session_state.get('figures_path', '.'))
                        if save_figure(fig, save_name, figures_path):
                            st.success(f"Map saved as {save_name}.png")
                
                plt.close()            

            st.markdown("---")
            
            #######################################################
            st.markdown("### Combined map for export")
            #######################################################
            
            required_indicators = ['L', 'M', 'N', 'R', 'T']
            available_indicators = [ind for ind in required_indicators if ind in filtered_env_plots.columns]
            
            if 'T' not in available_indicators:
                st.warning(f"Temperature indicator (T) not found in data. Available indicators: {available_indicators}")
            
            # Check if we have the original 4 indicators
            original_indicators = ['L', 'M', 'N', 'R']
            original_available = [ind for ind in original_indicators if ind in available_indicators]
            
            if len(original_available) < 4:
                st.warning(f"Need all 4 original indicators (L, M, N, R). Only found: {original_available}")
            else:
                # Define colormaps for each indicator
                indicator_colormaps = {
                    'L': 'YlGnBu_r',      # Light: dark to bright
                    'M': 'YlGnBu',       # Moisture: white to deep blue
                    'N': 'Greens',      # Nitrogen: represents nutrition
                    'R': 'RdYlBu_r',    # pH: red (acidic) to blue (alkaline)
                    'T': 'vlag'       # Temperature: cool to warm colors
                }
                
                indicator_titles = {
                    'L': 'Light',
                    'M': 'Moisture', 
                    'N': 'Nitrogen',
                    'R': 'Reaction',
                    'T': 'Temperature'
                }
                
                # Create figure with 3x2 subplots (A4 size: ~8.27 x 11.69 inches)
                fig, axes = plt.subplots(3, 2, figsize=(8.27, 11.69))
                fig.suptitle('Ellenberg Indicator Gradients', fontsize=14, y=0.97)
                
                # Define subplot positions
                positions = [(0,0), (0,1), (1,0), (1,1), (2,0)]  # L, M, N, R, T
                indicators_to_plot = ['L', 'M', 'N', 'R', 'T']
                
                for i, indicator in enumerate(indicators_to_plot):
                    row, col = positions[i]
                    ax = axes[row, col]
                    
                    # Add standard background elements
                    center = (0.5, 0.5)
                    radii = [0.125, 0.25, 0.375, 0.5]
                    for radius in radii:
                        circle = Circle(center, radius, linewidth=0.5, color='gray', fill=False, alpha=0.3)
                        ax.add_patch(circle)
                    
                    # Add guide lines
                    ax.add_line(Line2D([0.5, 0.5], [0, 1], color='gray', linewidth=0.5, alpha=0.3))
                    ax.add_line(Line2D([0, 1], [0.5, 0.5], color='gray', linewidth=0.5, alpha=0.3))
                    ax.add_line(Line2D([0, 1], [0, 1], color='gray', linewidth=0.5, alpha=0.3))
                    ax.add_line(Line2D([0, 1], [1, 0], color='gray', linewidth=0.5, alpha=0.3))
                    
                    # Check if indicator is available in data
                    if indicator in filtered_env_plots.columns:
                        # Filter data for this indicator
                        indicator_data = filtered_env_plots.dropna(subset=[indicator])
                        
                        if len(indicator_data) > 0:
                            # Create environmental gradient
                            try:
                                from scipy.interpolate import griddata
                                from scipy.ndimage import gaussian_filter
                                from scipy.spatial import ConvexHull
                                
                                # Create grid
                                xi = np.linspace(0, 1, 100)
                                yi = np.linspace(0, 1, 100)
                                xi, yi = np.meshgrid(xi, yi)
                                
                                # Get coordinates and values
                                points = indicator_data[['xcoor', 'ycoor']].values
                                values = indicator_data[indicator].values
                                
                                # Create convex hull and interpolate
                                hull = ConvexHull(points)
                                hull_path = MplPath(points[hull.vertices])
                                
                                zi = griddata(points, values, (xi, yi), method='nearest', fill_value=np.nan)
                                zi_smooth = gaussian_filter(zi, sigma=0.95)
                                
                                # Mask outside hull
                                grid_points = np.column_stack((xi.ravel(), yi.ravel()))
                                inside_hull = hull_path.contains_points(grid_points)
                                mask = inside_hull.reshape(xi.shape)
                                zi_smooth[~mask] = np.nan
                                
                                # Create contour plot with specific colormap
                                env_min = indicator_data[indicator].min()
                                env_max = indicator_data[indicator].max()
                                levels = np.linspace(env_min, env_max, 12)
                                
                                contour = ax.contourf(xi, yi, zi_smooth, levels=levels, 
                                                    cmap=indicator_colormaps[indicator], alpha=0.4)
                                
                                
                                if show_scatter_env:
                                    scatter = ax.scatter(
                                    indicator_data['xcoor'],  indicator_data['ycoor'],
                                    c=indicator_data[indicator], cmap=indicator_colormaps[indicator],
                                    s=1.5, alpha=1.0, edgecolors=(70/255, 80/255, 95/255, 0.9), linewidths=0.05
                                )
                                
                                # Add colorbar for this subplot
                                cbar = plt.colorbar(contour, ax=ax, shrink=0.75)
                                cbar.set_label(f'{indicator_titles[indicator]} Value', fontsize=10)
                                
                            except Exception as e:
                                # Fallback to scatter plot if gradient fails
                                scatter = ax.scatter(
                                    indicator_data['xcoor'], indicator_data['ycoor'],
                                    c=indicator_data[indicator], 
                                    cmap=indicator_colormaps[indicator],
                                    s=20, alpha=0.8, edgecolors='black', linewidths=0.2
                                )
                                
                                # Add colorbar for scatter plot
                                cbar = plt.colorbar(scatter, ax=ax, shrink=0.75)
                                cbar.set_label(f'{indicator_titles[indicator]} Value', fontsize=10)
                    else:
                        # If indicator not available, show message
                        ax.text(0.5, 0.5, f'{indicator_titles[indicator]}\nNot Available', 
                               ha='center', va='center', fontsize=12, 
                               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
                    
                    # Set subplot properties
                    ax.set_xlim(-0.05, 1.05)
                    ax.set_ylim(-0.05, 1.05)
                    ax.set_aspect('equal')
                    ax.set_title(indicator_titles[indicator], fontsize=12, pad=10)
                    
                    # Remove ticks and labels as requested
                    ax.set_xticks([])
                    ax.set_yticks([])
                    ax.set_xlabel('')
                    ax.set_ylabel('')
                
                # Handle the last subplot (bottom right) - keep empty for now
                ax_composite = axes[2, 1]
                ax_composite.set_xlim(-0.05, 1.05)
                ax_composite.set_ylim(-0.05, 1.05)
                ax_composite.set_aspect('equal')
                ax_composite.set_title('Composite Ellenberg', fontsize=12, pad=10)
                ax_composite.set_xticks([])
                ax_composite.set_yticks([])
                ax_composite.set_xlabel('')
                ax_composite.set_ylabel('')

                # Add standard background elements (same as other subplots)
                center = (0.5, 0.5)
                radii = [0.125, 0.25, 0.375, 0.5]
                for radius in radii:
                    circle = Circle(center, radius, linewidth=0.5, color='gray', fill=False, alpha=0.3)
                    ax_composite.add_patch(circle)

                # Add guide lines
                ax_composite.add_line(Line2D([0.5, 0.5], [0, 1], color='gray', linewidth=0.5, alpha=0.3))
                ax_composite.add_line(Line2D([0, 1], [0.5, 0.5], color='gray', linewidth=0.5, alpha=0.3))
                ax_composite.add_line(Line2D([0, 1], [0, 1], color='gray', linewidth=0.5, alpha=0.3))
                ax_composite.add_line(Line2D([0, 1], [1, 0], color='gray', linewidth=0.5, alpha=0.3))
                
                # Add annotated background with full opacity and default thresholds
                create_annotated_background(ax_composite, filtered_env_plots, text_alpha=0.85, line_alpha=0.30, nr_percentile=15, l_percentile=12.5, salt_distance=65)


                # Scale down text sizes for smaller subplot
                for text in ax_composite.texts:
                    current_size = text.get_fontsize()
                    if current_size >= 15:
                        text.set_fontsize(6)  # Scale down large text
                    elif current_size >= 10:
                        text.set_fontsize(6)  # Scale down medium text
                
                plt.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space for suptitle
                
                st.pyplot(fig)       
                
                save_name_4panel = st.text_input("Save 46-panel figure as:", 
                            value="Ellenberg overview", 
                            key="save_6panel")  
                # with col2:
                if st.button("💾 Save 6-Panel Figure", key="save_btn_4panel"):
                    figures_path = Path(st.session_state.get('figures_path', '.'))
                    st.write(figures_path)
                    if save_figure(fig, save_name_4panel, figures_path):
                        st.success(f"4-panel figure saved as {save_name_4panel}.png")
                
                plt.close()
                
            # else:
            #     st.warning(f"No valid data for {env_labels.get(selected_env, selected_env)}")

            ################################################
            # Ecological classification
            ################################################
            
            st.markdown("---")
            st.markdown("### 🗺️ Ecological Classification System")
            
            # Check if we have all required indicators
            required_indicators = ['L', 'M', 'N', 'R']
            available_indicators = [ind for ind in required_indicators if ind in filtered_env_plots.columns]
            
            if len(available_indicators) < 4:
                st.warning(f"Need all 4 indicators (L, M, N, R) for classification. Only found: {available_indicators}")
            else:
                st.markdown("""
                This analysis classifies plots into ecological types based on Ellenberg indicator values.
                Only plots with clear ecological preferences are classified:
                - **Moisture**: Dry (<4.5), Mesic (4.5-6.5), Wet (>6.5)
                - **Light**: Shaded (<5.15) vs Open (>5.25) 
                - **pH**: Acidic (<4.55) vs Basic (>4.65)
                - **Nitrogen**: Poor (<4.95) vs Rich (>5.05)
                
                *This creates 3 × 2 × 2 × 2 = 24 possible ecological classes.*
                """)
                
                # Create classification function
                def classify_plot(row):
                    """Classify plot based on Ellenberg values"""
                    # Handle missing values
                    if pd.isna(row['L']) or pd.isna(row['M']) or pd.isna(row['N']) or pd.isna(row['R']):
                        return None
                    
                    # Create classification code
                    if row['M'] < 4.5:
                        moisture = 'D'  # Dry
                    elif row['M'] > 6.5:
                        moisture = 'W'  # Wet
                    elif 4.5 <= row['M'] <= 6.5:
                        moisture = 'M'  # Mesic
                    else:
                        return None  # Should not occur with this logic

                    if row['L'] < 5.15:
                        light = 'S'  # Shaded
                    elif row['L'] > 5.25:
                        light = 'O'  # Open
                    else:
                        return None  # Intermediate, exclude

                    if row['R'] < 4.55:
                        ph = 'A'  # Acidic
                    elif row['R'] > 4.650:
                        ph = 'B'  # Basic
                    else:
                        return None  # Intermediate, exclude

                    if row['N'] < 4.95:
                        nitrogen = 'P'  # Poor
                    elif row['N'] > 5.05:
                        nitrogen = 'R'  # Rich
                    else:
                        return None  # Intermediate, exclude
                    
                    return f"{moisture}{light}{ph}{nitrogen}"
                
                # Apply classification
                classified_plots = filtered_env_plots.copy()
                classified_plots = classified_plots.dropna(subset=['L', 'M', 'N', 'R'])
                classified_plots['eco_class'] = classified_plots.apply(classify_plot, axis=1)
                
                # Remove any plots that couldn't be classified
                classified_plots = classified_plots.dropna(subset=['eco_class'])
                
                st.info(f"Successfully classified {len(classified_plots)} plots into ecological types")
                
                # Put classification summary and class guide in separate expanders
                with st.expander("📊 Classification Summary"):
                    class_counts = classified_plots['eco_class'].value_counts().sort_index()
                    st.markdown("**Classification Summary:**")
                    for eco_class, count in class_counts.items():
                        percentage = (count / len(classified_plots)) * 100
                        st.text(f"{eco_class}: {count} plots ({percentage:.1f}%)")
                
                with st.expander("📝 Class Code Guide"):
                    st.markdown("**Class Code Guide:**")
                    st.markdown("Position 1: **D**ry / **M**esic / **W**et")  
                    st.markdown("Position 2: **O**pen / **S**haded")
                    st.markdown("Position 3: **B**asic / **A**cidic") 
                    st.markdown("Position 4: **R**ich / **P**oor")
                    st.markdown("*Example: MSAP = Mesic-Shaded-Acidic-Poor*")
                
                # Visualization options
                st.markdown("### Visualization options")
                
                vis_type = st.radio(
                    "Choose visualization type:",
                    ["Scatter plot", "Kernel density estimation (KDE)"],
                    key="eco_vis_type"
                )
                
                # Color scheme selection
                color_scheme = st.selectbox(
                    "Select color scheme:",
                    ["Set3", "tab20", "viridis", "plasma", "coolwarm", "rainbow"],
                    key="eco_color_scheme"
                )
                
                # Four-column filtering by individual indicators
                st.markdown("**Filter by ecological indicators:**")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    moisture_filter = st.selectbox(
                        "Moisture:",
                        ["All", "Dry", "Mesic", "Wet"],
                        key="moisture_filter"
                    )
                
                with col2:
                    light_filter = st.selectbox(
                        "Light:",
                        ["All", "Shaded", "Open"],
                        key="light_filter"
                    )
                
                with col3:
                    ph_filter = st.selectbox(
                        "pH:",
                        ["All", "Acidic", "Basic"],
                        key="ph_filter"
                    )
                
                with col4:
                    nitrogen_filter = st.selectbox(
                        "Nitrogen:",
                        ["All", "Poor", "Rich"],
                        key="nitrogen_filter"
                    )
                
                # Apply indicator-based filtering
                filtered_by_indicators = classified_plots.copy()
                
                if moisture_filter != "All":
                    moisture_code = {"Dry": "D", "Mesic": "M", "Wet": "W"}[moisture_filter]
                    filtered_by_indicators = filtered_by_indicators[
                        filtered_by_indicators['eco_class'].str[0] == moisture_code
                    ]
                
                if light_filter != "All":
                    light_code = {"Shaded": "S", "Open": "O"}[light_filter]
                    filtered_by_indicators = filtered_by_indicators[
                        filtered_by_indicators['eco_class'].str[1] == light_code
                    ]
                
                if ph_filter != "All":
                    ph_code = {"Acidic": "A", "Basic": "B"}[ph_filter]
                    filtered_by_indicators = filtered_by_indicators[
                        filtered_by_indicators['eco_class'].str[2] == ph_code
                    ]
                
                if nitrogen_filter != "All":
                    nitrogen_code = {"Poor": "P", "Rich": "R"}[nitrogen_filter]
                    filtered_by_indicators = filtered_by_indicators[
                        filtered_by_indicators['eco_class'].str[3] == nitrogen_code
                    ]
                
                # Update class counts after indicator filtering
                filtered_class_counts = filtered_by_indicators['eco_class'].value_counts().sort_index()
                
                # Additional filtering by specific ecological classes
                selected_classes = st.multiselect(
                    "Further filter by specific ecological classes (leave empty for all from above selection):",
                    options=sorted(filtered_class_counts.index.tolist()),
                    key="eco_class_filter"
                )
                
                if selected_classes:
                    plot_data = filtered_by_indicators[filtered_by_indicators['eco_class'].isin(selected_classes)]
                    st.info(f"Showing {len(plot_data)} plots from selected classes")
                else:
                    plot_data = filtered_by_indicators
                    st.info(f"Showing {len(plot_data)} plots after indicator filtering")
                
                # Create the map
                fig, ax = create_base_map("Ecological Classification")
                
                if vis_type == "Scatter plot":
                    # Create scatter plot with different colors for each class
                    unique_classes = sorted(plot_data['eco_class'].unique())
                    
                    # Create color map
                    # import matplotlib.cm as cm
                    # import matplotlib.pyplot as plt
                    cmap = matplotlib.colormaps[color_scheme]
                    #cmap = cm.get_cmap(color_scheme)
                    colors = [cmap(i / len(unique_classes)) for i in range(len(unique_classes))]
                    
                    for i, eco_class in enumerate(unique_classes):
                        class_data = plot_data[plot_data['eco_class'] == eco_class]
                        ax.scatter(
                            class_data['xcoor'], class_data['ycoor'],
                            c=[colors[i]], label=eco_class,
                            s=40, alpha=0.7, edgecolors='black', linewidths=0.3
                        )
                    
                    # Add legend with multiple columns if many classes
                    if len(unique_classes) > 8:
                        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', ncol=2, fontsize=8)
                    else:
                        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
                
                else:  # KDE visualization
                    try:
                        from scipy.stats import gaussian_kde
                        import matplotlib.cm as cm
                        import numpy as np
                        from matplotlib.lines import Line2D
                        
                        # Create dynamic title based on selections
                        title_parts = []
                        
                        # Add ecological indicator filters to title
                        if moisture_filter != "All":
                            title_parts.append(f"Moisture: {moisture_filter}")
                        if light_filter != "All":
                            title_parts.append(f"Light: {light_filter}")
                        if ph_filter != "All":
                            title_parts.append(f"pH: {ph_filter}")
                        if nitrogen_filter != "All":
                            title_parts.append(f"Nitrogen: {nitrogen_filter}")
                        
                        # Add specific class selections to title
                        if selected_classes:
                            class_str = ", ".join(selected_classes)
                            title_parts.append(f"Classes: {class_str}")
                        
                        # Create final title
                        if title_parts:
                            # Extract just the values (remove the "Moisture:", "Light:" etc. labels)
                            simple_parts = []
                            for part in title_parts:
                                if ":" in part:
                                    simple_parts.append(part.split(": ")[1].lower())
                                else:
                                    simple_parts.append(part.lower())
                            kde_title = " - ".join(simple_parts)
                        else:
                            kde_title = "all ecological classes"
             
                        # KDE intensity slider
                        kde_bandwidth = st.slider(
                            "KDE smoothing (bandwidth):", 
                            0.01, 0.2, 0.15, 0.01,
                            key="kde_bandwidth"
                        )
                        
                        # Check if we have enough data points
                        if len(plot_data) > 2:  # Need at least 3 points for KDE
                            # Create grid for KDE
                            xi = np.linspace(0, 1, 100)
                            yi = np.linspace(0, 1, 100)
                            xi, yi = np.meshgrid(xi, yi)
                            
                            # Get all coordinates from selected plots (treat as single distribution)
                            points = plot_data[['xcoor', 'ycoor']].values
                            
                            # Create KDE for all selected points together
                            kde = gaussian_kde(points.T, bw_method=kde_bandwidth)
                            
                            # Evaluate on grid
                            grid_points = np.column_stack((xi.ravel(), yi.ravel()))
                            zi = kde(grid_points.T).reshape(xi.shape)

                            # Calculate true 50% and 90% contour levels using cumulative density
                            sorted_density = np.sort(zi.ravel())[::-1]  # Sort density values highest to lowest
                            cumsum = np.cumsum(sorted_density)
                            total = cumsum[-1]
                            if total > 0:  # Check we have valid density
                                level_90 = sorted_density[np.where(cumsum >= 0.9 * total)[0][0]]
                                level_50 = sorted_density[np.where(cumsum >= 0.5 * total)[0][0]]                            
                        
                                # Find center of distribution (maximum density point) - PUT IT HERE
                                # Find center using mean of actual data points
                                center_x = plot_data['xcoor'].mean()
                                center_y = plot_data['ycoor'].mean()
                                
                                # Use a consistent color (first color from selected scheme)
                                cmap = matplotlib.colormaps[color_scheme]
                                #cmap = cm.get_cmap(color_scheme)
                                color = cmap(0.3)  # Use a nice color from the palette
                                
                                # Draw 90% contour (outer boundary)
                                contour_90 = ax.contour(
                                    xi, yi, zi, 
                                    levels=[level_90],
                                    colors=['blue'],
                                    linewidths=2.5,
                                    linestyles='--',
                                    alpha=0.9
                                )
                                
                                # Draw 50% contour (inner boundary)
                                contour_50 = ax.contour(
                                    xi, yi, zi, 
                                    levels=[level_50],
                                    colors=['red'],
                                    linewidths=2.5,
                                    linestyles='-',
                                    alpha=0.99
                                )
                                
                                # Add individual plots as grey dots
                                ax.scatter(
                                    plot_data['xcoor'], plot_data['ycoor'],
                                    c='grey', s=12, alpha=0.35, edgecolors='none'
)
                                
                                # Add label at center
                                ax.text(center_x, center_y, kde_title, 
                                    fontsize=10, ha='center', va='center',
                                    bbox=dict(boxstyle='round,pad=0.4', 
                                            facecolor='white', 
                                            alpha=0.9,
                                            edgecolor=color))
                                
                                # Display center coordinates for copying
                                st.markdown("**Distribution Center (Landscape Coordinates):**")
                                coords_text = f"Center: ({center_x:.3f}, {center_y:.3f})\nSample size: {len(plot_data)} plots"
                                
                                st.text_area(
                                    "Center coordinates (copy-friendly format):",
                                    coords_text,
                                    height=68,
                                    key="center_coords"
                                )
                                
                                # Add legend for contour lines
                                legend_elements = [
                                    Line2D([0], [0], color=color, linewidth=2.5, linestyle='-', 
                                           label='50% boundary'),
                                    Line2D([0], [0], color=color, linewidth=1.5, linestyle='--', 
                                           label='90% boundary')
                                ]
                                ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
                            
                            else:
                                st.warning("No valid density values found for KDE visualization")
                        
                        else:
                            st.warning(f"Need at least 3 data points for KDE visualization. Currently have {len(plot_data)} plots.")
                        
                    except Exception as e:
                        st.error(f"Could not create KDE visualization: {str(e)}")
                        st.info("Falling back to scatter plot")
                        
                        # Fallback to scatter plot
                        import matplotlib.cm as cm
                        cmap = matplotlib.colormaps[color_scheme]
                        #cmap = cm.get_cmap(color_scheme)
                        
                        ax.scatter(
                            plot_data['xcoor'], plot_data['ycoor'],
                            c=[cmap(0.3)], 
                            s=40, alpha=0.7, edgecolors='black', linewidths=0.3
                        )
                
                # Zoom control
                zoom = st.slider("Zoom:", -0.1, 0.25, -0.05, key="eco_zoom")
                ax.set_xlim(zoom, 1 - zoom)
                ax.set_ylim(zoom, 1 - zoom)
                
                st.pyplot(fig)
                
                # Export options
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    save_name_eco = st.text_input("Save map as:", 
                                                value="ecological_classification", 
                                                key="save_eco")
                with col2:
                    if st.button("💾 Save Map", key="save_btn_eco"):
                        figures_path = Path(st.session_state.get('figures_path', '.'))
                        if save_figure(fig, save_name_eco, figures_path):
                            st.success(f"Map saved as {save_name_eco}.png")
                
                with col3:
                    # Download classification data
                    if st.button("📊 Export Data", key="export_eco_data"):
                        # Prepare data for export
                        export_data = plot_data[['xcoor', 'ycoor', 'L', 'M', 'N', 'R', 'eco_class']].copy()
                        
                        # Convert to CSV
                        csv = export_data.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"ecological_classification_{len(export_data)}_plots.csv",
                            mime="text/csv"
                        )
                
                plt.close()
                
                # Helper function to highlight dominant values in dataframe
                def highlight_dominant(df):
                    """Create a styled dataframe highlighting dominant values"""
                    def highlight_max(row):
                        # Skip 'Total' row
                        if row.name == 'Total':
                            return [''] * len(row)
                        
                        # Find max value (excluding 'Total' column if present)
                        if 'Total' in row.index:
                            row_values = row.drop('Total')
                        else:
                            row_values = row
                        
                        if len(row_values) == 0 or row_values.max() == 0:
                            return [''] * len(row)
                        
                        # Create style array
                        styles = [''] * len(row)
                        max_col_pos = row_values.idxmax()
                        max_pos = row.index.get_loc(max_col_pos)
                        styles[max_pos] = 'font-weight: bold; background-color: #ffeb3b'
                        
                        return styles
                    
                    return df.style.apply(highlight_max, axis=1)
                
                # Additional analysis: Show which major habitat types fall into each ecological class
                if 'major_type' in classified_plots.columns:
                    st.markdown("### Ecological classes by major habitat type")
                    
                    # Create cross-tabulation for major types
                    crosstab_major = pd.crosstab(classified_plots['major_type'], 
                                               classified_plots['eco_class'], 
                                               margins=True, margins_name="Total")
                    
                    # Apply highlighting and display as styled table
                    styled_major = highlight_dominant(crosstab_major)
                    #styled_major['naturtypeId'] = styled_major['naturtypeId'].astype(str)
                    st.dataframe(styled_major)
                
                # Additional table for detailed habitat types
                if 'naturtypeId' in classified_plots.columns:
                    st.markdown("### Ecological classes by detailed habitat type (naturtypeId)")
                    
                    # Create cross-tabulation for detailed habitat types
                    crosstab_detailed = pd.crosstab(classified_plots['naturtypeId'], 
                                                  classified_plots['eco_class'], 
                                                  margins=True, margins_name="Total")
                    crosstab_detailed.index = crosstab_detailed.index.astype(str)
                    
                    # Apply highlighting and display as styled table
                    styled_detailed = highlight_dominant(crosstab_detailed)
                    st.dataframe(styled_detailed)
                    
                    # Optional: Show only habitat types with more than a minimum number of plots
                    min_plots = st.number_input(
                        "Show only habitat types with at least this many plots:",
                        min_value=1,
                        max_value=100,
                        value=5,
                        key="min_plots_habitat"
                    )
                    
                    # Filter habitat types by minimum plot count
                    habitat_counts = classified_plots['naturtypeId'].value_counts()
                    filtered_habitats = habitat_counts[habitat_counts >= min_plots].index
                    
                    if len(filtered_habitats) < len(habitat_counts):
                        st.markdown(f"### Filtered view: habitat types with ≥{min_plots} plots")
                        
                        filtered_data = classified_plots[classified_plots['naturtypeId'].isin(filtered_habitats)]
                        crosstab_filtered = pd.crosstab(filtered_data['naturtypeId'], 
                                                      filtered_data['eco_class'], 
                                                      margins=True, margins_name="Total")
                        crosstab_filtered.index = crosstab_filtered.index.astype(str)
                        
                        # Apply highlighting to filtered table
                        styled_filtered = highlight_dominant(crosstab_filtered)
                        st.dataframe(styled_filtered)
                        
                        # Show summary statistics
                        st.markdown(f"**Summary:** Showing {len(filtered_habitats)} habitat types out of {len(habitat_counts)} total types")
                        st.markdown(f"**Coverage:** {len(filtered_data)} plots out of {len(classified_plots)} total plots ({len(filtered_data)/len(classified_plots)*100:.1f}%)")
    


    with tab4:
        st.markdown("### 🗺️ Habitat Distribution Overview")
        st.markdown("*Visualizing the geographic distribution boundaries of major habitat types*")
        
        # Check if we have the required data
        if 'major_type' not in plot_df.columns:
            st.error("No major_type data available for habitat overview")
        else:
            # Get unique major types and their counts
            major_type_counts = plot_df['major_type'].value_counts()
            st.info(f"Found {len(major_type_counts)} major habitat types")
            
            # Display major type counts
            with st.expander("📊 Major Type Summary", expanded=False):
                col1, col2 = st.columns(2)
                mid_point = len(major_type_counts) // 2
                
                with col1:
                    for i, (major_type, count) in enumerate(major_type_counts.iloc[:mid_point].items()):
                        st.write(f"**{major_type}**: {count:,} plots")
                
                with col2:
                    for i, (major_type, count) in enumerate(major_type_counts.iloc[mid_point:].items()):
                        st.write(f"**{major_type}**: {count:,} plots")
            
            # Settings for the overview map
            st.markdown("#### ⚙️ Map Settings")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                density_threshold = st.slider(
                    "Percentage of plots within boundary:",
                    min_value=10,
                    max_value=90,
                    value=50,
                    step=5,
                    help="50% means boundary contains 50% of plots for each major type. Higher values = tighter boundaries."
                )
                
                min_plots_for_kde = st.slider(
                    "Minimum plots for boundary:",
                    min_value=5,
                    max_value=50,
                    value=10,
                    help="Major types with fewer plots won't get boundaries"
                )
            
            with col2:
                show_plot_points = st.checkbox("Show individual plots", value=False)
                show_boundaries = st.checkbox("Show habitat boundaries", value=True)
                show_labels = st.checkbox("Show habitat labels", value=True)
                
            with col3:
                zoom_overview = st.slider("Zoom:", -0.1, 0.25, -0.05, key="overview_zoom")
                label_fontsize = st.slider("Label font size:", 6, 14, 10)
            
            # Filter data and remove NaN major_types and unwanted types
            excluded_types = ['Unknown Type', 'Marine naturtype', 'Marine naturtyper', 'Søer og vandløb', 'Unknown type']
            all_background_data = plot_df.dropna(subset=['major_type', 'xcoor', 'ycoor'])
            all_background_data = all_background_data[~all_background_data['major_type'].isin(excluded_types)]
            
            # Get available major types for selection (from the cleaned background data)
            available_major_types = sorted(all_background_data['major_type'].unique())
            
            # Major type selection
            st.markdown("#### 🎯 Select Major Types to Display")
            selected_major_types_overview = st.multiselect(
                "Choose which major habitat types to show:",
                options=available_major_types,
                default=available_major_types,  # All non-excluded types selected by default
                help="Select one or more major types to display on the overview map"
            )
            
            # select preferred background here
            show_background_annotated = st.checkbox("Show background (annotated)", value=False, key='backAnno')
            show_background_plot = st.checkbox("Show background (plots as points)", value=False, key='backPoint')
            
            # Annotation transparency controls (only show if annotated background is enabled)
            if show_background_annotated:
                text_alpha = st.slider("Text transparency:", 0.0, 1.0, 0.7, 0.05, key="text_alpha")
                line_alpha = st.slider("Overlay transparency:", 0.0, 1.0, 0.2, 0.05, key="line_alpha")
                nr_percentile = st.slider("N/R threshold (%):", 5, 25, 15, 1, key="nr_percentile4",
                    help="Percentile for nutrient-poor/low-pH zones. Lower = more extreme conditions only.")
                l_percentile = st.slider("Light threshold (%):", 5.0, 25.0, 12.5, 0.5, key="l_percentile4",
                    help="Percentile for shade/forest zones. Lower = darker shade only.")
                salt_distance = st.slider("Salt zone extent (%):", 50, 90, 65, 5, key="salt_distance4",
                    help="Distance cutoff for halophytic zones. Higher = tighter boundaries around core.")

            # Filter data for boundaries/labels based on selection (but keep all background data)
            if selected_major_types_overview:
                overview_data = all_background_data[all_background_data['major_type'].isin(selected_major_types_overview)]
                st.info(f"Selected {len(selected_major_types_overview)} major types with {len(overview_data)} total plots")
            else:
                st.warning("Please select at least one major type to display")
                st.stop()

            if len(overview_data) == 0:
                st.error("No valid plot data with coordinates and major_type information")
            else:
                # Create the overview map
                fig_overview, ax_overview = create_base_map(" . ", figsize=(14, 14))


                # plot background - all plots in light grey (regardless of selection)
                if show_background_plot:
                    ax_overview.scatter(
                        all_background_data['xcoor'], all_background_data['ycoor'],
                        s=25, alpha=0.3, c='lightgrey',
                        edgecolors='none'
                    )

                # Add annotated background if requested (after basic background, before other layers)
                if show_background_annotated:
                    create_annotated_background(ax_overview, plot_df, text_alpha, line_alpha, nr_percentile, l_percentile, salt_distance)
                
                # Get color palette for selected major types with better visibility
                unique_major_types = sorted(overview_data['major_type'].unique())
                
                # Use a more vibrant color palette that avoids light colors
                if len(unique_major_types) <= 10:
                    # For smaller number of types, use distinct, bright colors
                    colors = sns.color_palette(['#e31a1c', '#1f78b4', '#33a02c', '#ff7f00', 
                                            '#6a3d9a', '#b15928', '#a6cee3', '#fb9a99', 
                                            '#b2df8a', '#fdbf6f'], len(unique_major_types))
                else:
                    # For larger number, use HSV which gives good separation
                    colors = sns.color_palette('hsv', len(unique_major_types))
                
                # Store information about processed boundaries
                boundary_info = []
                
                # Process each major type
                for i, major_type in enumerate(unique_major_types):
                    major_data = overview_data[overview_data['major_type'] == major_type]
                    n_plots = len(major_data)
                    
                    # Skip if not enough data for KDE
                    if n_plots < min_plots_for_kde:
                        st.warning(f"Skipping {major_type}: only {n_plots} plots (need ≥{min_plots_for_kde})")
                        continue
                    
                    try:
                        # Show individual plots for this major type if requested
                        if show_plot_points:
                            ax_overview.scatter(
                                major_data['xcoor'], major_data['ycoor'],
                                s=5, alpha=0.3, c=[colors[i]],
                                label=f"{major_type} ({n_plots} plots)"
                            )
                        
                        # Create KDE and extract contours for shading
                        
                        # Create KDE directly on the main plot with fill
                        if show_boundaries:
                            kde_quantile = (100 - density_threshold) / 100
                            
                            # Create KDE plot and capture the contour collection
                            kde_contours = sns.kdeplot(
                                data=major_data, x='xcoor', y='ycoor',
                                fill=True, thresh=kde_quantile, levels=2,
                                color=colors[i], alpha=0.4,
                                ax=ax_overview
                            )
                            
                            # Extract contour paths directly from the plot we just created
                            if show_labels:
                                contour_paths = []
                                for collection in ax_overview.collections[-2:]:  # Get the last collections added
                                    for path in collection.get_paths():
                                        if len(path.vertices) > 3:
                                            contour_paths.append(path.vertices)
                                
                                if contour_paths:
                                    largest_contour = max(contour_paths, key=lambda x: len(x))
                                    
                                    # Calculate centroid
                                    centroid_x = np.mean(largest_contour[:, 0])
                                    centroid_y = np.mean(largest_contour[:, 1])
                                    centroid_x = max(0.05, min(0.95, centroid_x))
                                    centroid_y = max(0.05, min(0.95, centroid_y))
                                    
                                    # Add label
                                    ax_overview.text(
                                        centroid_x, centroid_y, major_type,
                                        fontsize=label_fontsize,
                                        ha='center', va='center',
                                        color='black',
                                        weight='bold',
                                        bbox=dict(boxstyle="round,pad=0.3", facecolor="none", alpha=0.8, edgecolor='none')
                                    )                        
                        
                                    
                                    # Store boundary info
                                    boundary_info.append({
                                        'major_type': major_type,
                                        'n_plots': n_plots,
                                        'centroid_x': centroid_x,
                                        'centroid_y': centroid_y,
                                        'boundary_points': len(largest_contour)
                                    })

                    except Exception as e:
                        st.warning(f"Error processing {major_type}: {str(e)}")
                        continue
                
                # Adjust zoom
                ax_overview.set_xlim(zoom_overview, 1 - zoom_overview)
                ax_overview.set_ylim(zoom_overview, 1 - zoom_overview)
                
                # Add legend if showing plot points
                if show_plot_points and len(unique_major_types) <= 15:
                    ax_overview.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
                                    fontsize=8, ncol=1)
                
                # Add summary text
                ax_overview.text(0.02, 0.92, 
                            f"Background plots: {len(all_background_data):,}\n" +
                            f"Selected types: {len(selected_major_types_overview)}\n" +
                            f"Boundaries shown: {len(boundary_info)}\n" +
                            f"Boundary contains: {density_threshold}% of plots",
                            transform=ax_overview.transAxes, 
                            verticalalignment='bottom',
                            fontsize=10,
                            bbox=dict(boxstyle="round,pad=0.5", 
                                    facecolor="white", alpha=0.9))
                
                # Display the map
                st.pyplot(fig_overview)
                
                # Save option
                col1, col2 = st.columns([2, 1])
                with col1:
                    save_name_overview = st.text_input(
                        "Save as:", 
                        value="habitat_distribution_overview", 
                        key="save_overview"
                    )
                with col2:
                    if st.button("💾 Save Map", key="save_btn_overview"):
                        figures_path = Path(st.session_state.get('figures_path', '.'))
                        if save_figure(fig_overview, save_name_overview, figures_path):
                            st.success(f"Map saved as {save_name_overview}.png")
                
                plt.close()
                
                # Show boundary statistics
                if boundary_info:
                    with st.expander("📊 Boundary Statistics", expanded=False):
                        boundary_df = pd.DataFrame(boundary_info)
                        
                        st.markdown("**Successfully processed major types:**")
                        st.dataframe(
                            boundary_df[['major_type', 'n_plots', 'boundary_points']],
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Summary statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Boundaries Created", len(boundary_info))
                        with col2:
                            st.metric("Total Plots", boundary_df['n_plots'].sum())
                        with col3:
                            st.metric("Avg Plots per Type", f"{boundary_df['n_plots'].mean():.0f}")
                
                # Geographic version if UTM coordinates available
                if 'UTMx' in overview_data.columns and 'UTMy' in overview_data.columns:
                    st.markdown("---")
                    st.markdown("### 🌍 Geographic Habitat Overview")
                    
                    geo_overview_data = overview_data.dropna(subset=['UTMx', 'UTMy'])
                    
                    if len(geo_overview_data) > 0:
                        show_geo_overview = st.checkbox("Show geographic habitat overview", value=False)
                        
                        if show_geo_overview:
                            # Geographic settings
                            col1, col2 = st.columns(2)
                            with col1:
                                geo_density_threshold = st.slider(
                                    "Geographic density threshold:",
                                    min_value=0.01,
                                    max_value=0.1,
                                    value=0.05,
                                    step=0.01,
                                    help="Lower values create tighter boundaries"
                                )
                            with col2:
                                geo_label_fontsize = st.slider("Geographic label size:", 8, 16, 12)
                            
                            # Create geographic overview
                            fig_geo_overview, ax_geo_overview = plt.subplots(figsize=(14, 12))
                            
                            # Load and plot Denmark background if available
                            if 'df_regional_pool' in st.session_state:
                                dk_dot_map = st.session_state['df_regional_pool']
                                ax_geo_overview.scatter(
                                    dk_dot_map['utm_easting'],
                                    dk_dot_map['utm_northing'],
                                    s=15, alpha=0.08, c='lightgrey',
                                    edgecolors='none'
                                )
                            
                            # Plot background - all plots (excluding unwanted types)
                            geo_overview_data = overview_data.dropna(subset=['UTMx', 'UTMy'])
                            ax_geo_overview.scatter(
                                geo_overview_data['UTMx'], geo_overview_data['UTMy'],
                                s=20, alpha=0.4, c='darkgrey',
                                edgecolors='none'
                            )
                            
                            # Process each selected major type for geographic boundaries
                            geo_boundary_info = []
                            
                            for i, major_type in enumerate(selected_major_types_overview):
                                major_geo_data = geo_overview_data[geo_overview_data['major_type'] == major_type]
                                
                                if len(major_geo_data) < min_plots_for_kde:
                                    continue
                                
                                try:
                                    # Convert percentage to quantile for geographic KDE
                                    geo_kde_quantile = (100 - geo_density_threshold) / 100
                                    
                                    # Create KDE for geographic coordinates
                                    fig_temp_geo, ax_temp_geo = plt.subplots()
                                    
                                    sns.kdeplot(
                                        data=major_geo_data, x='UTMx', y='UTMy',
                                        fill=False, thresh=geo_kde_quantile,
                                        ax=ax_temp_geo
                                    )
                                    
                                    # Extract contour paths
                                    geo_contour_paths = []
                                    for collection in ax_temp_geo.collections:
                                        for path in collection.get_paths():
                                            if len(path.vertices) > 3:
                                                geo_contour_paths.append(path.vertices)
                                    
                                    plt.close(fig_temp_geo)
                                    
                                    # Plot largest contour with better visibility
                                    if geo_contour_paths:
                                        largest_geo_contour = max(geo_contour_paths, key=lambda x: len(x))
                                        
                                        boundary_utm_x = largest_geo_contour[:, 0]
                                        boundary_utm_y = largest_geo_contour[:, 1]
                                        
                                        # Close the polygon
                                        boundary_utm_x = np.append(boundary_utm_x, boundary_utm_x[0])
                                        boundary_utm_y = np.append(boundary_utm_y, boundary_utm_y[0])
                                        
                                        ax_geo_overview.plot(
                                            boundary_utm_x, boundary_utm_y,
                                            color=colors[i], linewidth=3.5, alpha=0.9
                                        )
                                        
                                        # Add label at centroid
                                        centroid_utm_x = np.mean(boundary_utm_x[:-1])
                                        centroid_utm_y = np.mean(boundary_utm_y[:-1])
                                        
                                        ax_geo_overview.text(
                                            centroid_utm_x, centroid_utm_y, major_type,
                                            fontsize=geo_label_fontsize,
                                            ha='center', va='center',
                                            color='black'
                                        )
                                        
                                        geo_boundary_info.append({
                                            'major_type': major_type,
                                            'n_plots': len(major_geo_data),
                                            'utm_centroid_x': centroid_utm_x,
                                            'utm_centroid_y': centroid_utm_y
                                        })
                                
                                except Exception as e:
                                    continue
                            
                            # Set geographic map properties
                            ax_geo_overview.set_xlabel('UTM X (meters)', fontsize=12)
                            ax_geo_overview.set_ylabel('UTM Y (meters)', fontsize=12)
                            ax_geo_overview.set_title('Geographic Distribution of Major Habitat Types', fontsize=16, pad=20)
                            ax_geo_overview.grid(True, alpha=0.3)
                            ax_geo_overview.set_aspect('equal', adjustable='box')
                            
                            # Add summary
                            ax_geo_overview.text(0.02, 0.98, 
                                            f"Selected types: {len(selected_major_types_overview)}\n" +
                                            f"Geographic boundaries: {len(geo_boundary_info)}\n" +
                                            f"Total plots: {len(geo_overview_data):,}",
                                            transform=ax_geo_overview.transAxes, 
                                            verticalalignment='top',
                                            fontsize=12,
                                            bbox=dict(boxstyle="round,pad=0.5", 
                                                    facecolor="white", alpha=0.9))
                            
                            st.pyplot(fig_geo_overview)
                            
                            # Save option for geographic overview
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                save_name_geo_overview = st.text_input(
                                    "Save geographic overview as:", 
                                    value="geographic_habitat_overview", 
                                    key="save_geo_overview"
                                )
                            with col2:
                                if st.button("💾 Save Geographic Map", key="save_btn_geo_overview"):
                                    figures_path = Path(st.session_state.get('figures_path', '.'))
                                    if save_figure(fig_geo_overview, save_name_geo_overview, figures_path):
                                        st.success(f"Geographic map saved as {save_name_geo_overview}.png")
                            
                            plt.close()
                    else:
                        st.info("No valid geographic coordinates for habitat overview")
                else:
                    st.info("Geographic coordinates not available for habitat overview")


else:
    st.info("👆 Please load a map database to begin plot analysis")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #7f8c8d; font-size: 0.9em;'>
    Habitat mapping
    </div>
    """, 
    unsafe_allow_html=True
)