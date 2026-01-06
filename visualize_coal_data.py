#!/usr/bin/env python3
"""visualize_coal_data.py - Generate coal seam visualizations for CBM assessment"""

import csv
import os
from dataclasses import dataclass
from typing import Optional

# Domain-based bounds for data validation (conservative - flagging, not removing)
THICKNESS_MIN = 0.0      # ft - can't be negative
THICKNESS_MAX = 50.0     # ft - catches obvious data entry errors (typical seams 0.5-8 ft)
DEPTH_MIN = 0.0          # ft - can't be above surface
DEPTH_MAX = 2500.0       # ft - deeper than expected for study area

# Study area bounds
STUDY_LAT_MIN, STUDY_LAT_MAX = 38.5, 39.6
STUDY_LON_MIN, STUDY_LON_MAX = -88.5, -87.3

# Coal seam configuration
SEAMS = {
    'herrin': {'top_col': 'TOP_HERRIN', 'thick_col': 'THICK_HERRIN', 'name': 'Herrin (No. 6)'},
    'springfield': {'top_col': 'TOP_SPRING', 'thick_col': 'THICK_SPRING', 'name': 'Springfield (No. 5)'},
    'danville': {'top_col': 'TOP_DANVILLE', 'thick_col': 'THICK_DANVILLE', 'name': 'Danville'},
    'colchester': {'top_col': 'TOP_COLCH', 'thick_col': 'THICK_COLCH', 'name': 'Colchester'},
    'seelyville': {'top_col': 'TOP_SEELY', 'thick_col': 'THICK_SEELY', 'name': 'Seelyville'},
}

@dataclass
class DrillHole:
    """Single drill hole record with coal seam data"""
    ids: str
    county: str
    lon: float
    lat: float
    surfelv: float
    thickness: Optional[float]  # For current seam
    depth: Optional[float]      # Calculated: surfelv - top elevation
    is_outlier: bool = False
    outlier_reason: str = ''


def parse_float(val: str) -> Optional[float]:
    """Parse string to float, return None if empty/invalid"""
    if val is None or val.strip() == '':
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def load_drill_holes(csv_path: str, seam_key: str) -> tuple[list[DrillHole], dict]:
    """Load drill hole data for a specific seam with validation"""
    seam = SEAMS[seam_key]
    holes = []
    stats = {
        'total_rows': 0,
        'valid_coords': 0,
        'has_thickness': 0,
        'has_depth': 0,
        'outliers_thickness': 0,
        'outliers_depth': 0,
        'outliers_coords': 0,
    }

    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats['total_rows'] += 1

            # Parse coordinates
            lon = parse_float(row.get('LONGITUDE', ''))
            lat = parse_float(row.get('LATITUDE', ''))
            surfelv = parse_float(row.get('SURFELV', ''))

            if lon is None or lat is None:
                continue
            stats['valid_coords'] += 1

            # Parse seam-specific data
            top_elev = parse_float(row.get(seam['top_col'], ''))
            thickness = parse_float(row.get(seam['thick_col'], ''))

            # Calculate depth from surface
            depth = None
            if surfelv is not None and top_elev is not None:
                depth = surfelv - top_elev

            # Create drill hole record
            hole = DrillHole(
                ids=row.get('IDS', ''),
                county=row.get('COUNTY_NAME', ''),
                lon=lon,
                lat=lat,
                surfelv=surfelv or 0,
                thickness=thickness,
                depth=depth,
            )

            # Check for outliers
            if not (STUDY_LON_MIN <= lon <= STUDY_LON_MAX and
                    STUDY_LAT_MIN <= lat <= STUDY_LAT_MAX):
                hole.is_outlier = True
                hole.outlier_reason = 'coords_outside_study_area'
                stats['outliers_coords'] += 1
            elif thickness is not None:
                if thickness < THICKNESS_MIN or thickness > THICKNESS_MAX:
                    hole.is_outlier = True
                    hole.outlier_reason = f'thickness={thickness:.1f}'
                    stats['outliers_thickness'] += 1
            elif depth is not None:
                if depth < DEPTH_MIN or depth > DEPTH_MAX:
                    hole.is_outlier = True
                    hole.outlier_reason = f'depth={depth:.0f}'
                    stats['outliers_depth'] += 1

            # Track stats
            if thickness is not None:
                stats['has_thickness'] += 1
            if depth is not None:
                stats['has_depth'] += 1

            holes.append(hole)

    return holes, stats


def filter_valid(holes: list[DrillHole], require_thickness: bool = False,
                 require_depth: bool = False, exclude_outliers: bool = True) -> list[DrillHole]:
    """Filter drill holes based on criteria"""
    result = []
    for h in holes:
        if exclude_outliers and h.is_outlier:
            continue
        if require_thickness and h.thickness is None:
            continue
        if require_depth and h.depth is None:
            continue
        result.append(h)
    return result


# Study counties for highlighting
STUDY_COUNTIES = {'CRAWFORD', 'CLARK', 'LAWRENCE', 'JASPER', 'CUMBERLAND', 'RICHLAND'}


import shapefile  # pyshp


def load_county_boundaries(shp_path: str, study_counties: set[str] = None) -> list[dict]:
    """Load county boundary polygons from shapefile"""
    sf = shapefile.Reader(shp_path)
    counties = []

    for shape_rec in sf.shapeRecords():
        name = shape_rec.record['COUNTY_NAM']  # Field name from the shapefile
        if study_counties and name.upper() not in study_counties:
            continue

        # Get polygon points
        points = shape_rec.shape.points
        # Handle multi-part polygons
        parts = list(shape_rec.shape.parts) + [len(points)]

        polygons = []
        for i in range(len(parts) - 1):
            poly_points = points[parts[i]:parts[i+1]]
            polygons.append(poly_points)

        counties.append({
            'name': name,
            'polygons': polygons,
        })

    return counties


import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import numpy as np


def plot_county_boundaries(ax, counties: list[dict], study_counties: set[str] = None):
    """Draw county boundaries on matplotlib axis"""
    for county in counties:
        for poly_points in county['polygons']:
            xs = [p[0] for p in poly_points]
            ys = [p[1] for p in poly_points]
            ax.plot(xs, ys, 'k-', linewidth=0.5, alpha=0.7)

            # Highlight study counties
            if study_counties and county['name'].upper() in study_counties:
                ax.fill(xs, ys, alpha=0.05, color='blue')


def create_thickness_map(holes: list[DrillHole], seam_name: str,
                         counties: list[dict], output_path: str):
    """Create static thickness map with county boundaries"""
    # Filter to holes with thickness data
    valid = [h for h in holes if h.thickness is not None and not h.is_outlier]
    outliers = [h for h in holes if h.thickness is not None and h.is_outlier]

    if not valid:
        print(f"  No valid thickness data for {seam_name}")
        return

    fig, ax = plt.subplots(figsize=(12, 10))

    # Plot county boundaries first
    plot_county_boundaries(ax, counties, STUDY_COUNTIES)

    # Extract data for plotting
    lons = [h.lon for h in valid]
    lats = [h.lat for h in valid]
    thicks = [h.thickness for h in valid]

    # Create scatter plot with sequential colormap
    scatter = ax.scatter(lons, lats, c=thicks, cmap='YlOrRd',
                         s=20, alpha=0.7, edgecolors='none',
                         vmin=0, vmax=max(8, max(thicks)))

    # Plot outliers in gray
    if outliers:
        out_lons = [h.lon for h in outliers]
        out_lats = [h.lat for h in outliers]
        ax.scatter(out_lons, out_lats, c='gray', s=10, alpha=0.3,
                   marker='x', label=f'Outliers ({len(outliers)})')

    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('Thickness (ft)', fontsize=12)

    # Labels and title
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.set_title(f'{seam_name} Coal - Thickness Map\n'
                 f'({len(valid)} points, {len(outliers)} outliers excluded)',
                 fontsize=14)

    # Set aspect ratio for geographic data
    ax.set_aspect('equal')

    if outliers:
        ax.legend(loc='lower right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")


def create_depth_map(holes: list[DrillHole], seam_name: str,
                     counties: list[dict], output_path: str):
    """Create static depth map highlighting optimal CBM range (500-1000 ft)"""
    # Filter to holes with depth data
    valid = [h for h in holes if h.depth is not None and not h.is_outlier]
    outliers = [h for h in holes if h.depth is not None and h.is_outlier]

    if not valid:
        print(f"  No valid depth data for {seam_name}")
        return

    fig, ax = plt.subplots(figsize=(12, 10))

    # Plot county boundaries
    plot_county_boundaries(ax, counties, STUDY_COUNTIES)

    # Separate into optimal range and outside
    optimal = [h for h in valid if 500 <= h.depth <= 1000]
    shallow = [h for h in valid if h.depth < 500]
    deep = [h for h in valid if h.depth > 1000]

    # Plot with different colors for depth ranges
    if shallow:
        ax.scatter([h.lon for h in shallow], [h.lat for h in shallow],
                   c=[h.depth for h in shallow], cmap='Blues',
                   s=15, alpha=0.5, vmin=0, vmax=500, label=f'Shallow <500ft ({len(shallow)})')

    if optimal:
        ax.scatter([h.lon for h in optimal], [h.lat for h in optimal],
                   c=[h.depth for h in optimal], cmap='Greens',
                   s=25, alpha=0.8, vmin=500, vmax=1000,
                   edgecolors='darkgreen', linewidths=0.5,
                   label=f'Optimal 500-1000ft ({len(optimal)})')

    if deep:
        ax.scatter([h.lon for h in deep], [h.lat for h in deep],
                   c=[h.depth for h in deep], cmap='Oranges',
                   s=15, alpha=0.5, vmin=1000, vmax=2000, label=f'Deep >1000ft ({len(deep)})')

    # Labels and title
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.set_title(f'{seam_name} Coal - Depth from Surface\n'
                 f'Optimal CBM range: 500-1000 ft (green)',
                 fontsize=14)

    ax.set_aspect('equal')
    ax.legend(loc='lower right', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")


def create_histogram(holes: list[DrillHole], seam_name: str, output_path: str):
    """Create histogram of thickness and depth distribution"""
    valid_thick = [h.thickness for h in holes if h.thickness is not None and not h.is_outlier]
    valid_depth = [h.depth for h in holes if h.depth is not None and not h.is_outlier]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Thickness histogram
    if valid_thick:
        axes[0].hist(valid_thick, bins=30, color='coral', edgecolor='black', alpha=0.7)
        axes[0].axvline(np.median(valid_thick), color='red', linestyle='--',
                        label=f'Median: {np.median(valid_thick):.2f} ft')
        axes[0].set_xlabel('Thickness (ft)', fontsize=12)
        axes[0].set_ylabel('Count', fontsize=12)
        axes[0].set_title(f'{seam_name} - Thickness Distribution (n={len(valid_thick)})')
        axes[0].legend()
    else:
        axes[0].text(0.5, 0.5, 'No thickness data', ha='center', va='center')
        axes[0].set_title(f'{seam_name} - Thickness Distribution')

    # Depth histogram with optimal range highlighted
    if valid_depth:
        n, bins, patches = axes[1].hist(valid_depth, bins=30, color='steelblue',
                                         edgecolor='black', alpha=0.7)
        # Highlight optimal range
        for i, (b, patch) in enumerate(zip(bins[:-1], patches)):
            if 500 <= b <= 1000:
                patch.set_facecolor('green')
                patch.set_alpha(0.8)

        axes[1].axvline(500, color='green', linestyle='--', alpha=0.7)
        axes[1].axvline(1000, color='green', linestyle='--', alpha=0.7)
        axes[1].axvline(np.median(valid_depth), color='red', linestyle='-',
                        label=f'Median: {np.median(valid_depth):.0f} ft')
        axes[1].set_xlabel('Depth from Surface (ft)', fontsize=12)
        axes[1].set_ylabel('Count', fontsize=12)
        axes[1].set_title(f'{seam_name} - Depth Distribution (n={len(valid_depth)})\n'
                          f'Green = Optimal CBM range (500-1000 ft)')
        axes[1].legend()
    else:
        axes[1].text(0.5, 0.5, 'No depth data', ha='center', va='center')
        axes[1].set_title(f'{seam_name} - Depth Distribution')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")


import folium
from folium.plugins import MarkerCluster


def get_thickness_color(thickness: float, max_thick: float = 8.0) -> str:
    """Return color for thickness value (yellow to red sequential)"""
    if thickness is None:
        return 'gray'
    # Normalize to 0-1
    norm = min(thickness / max_thick, 1.0)
    # Yellow (255,255,0) to Red (255,0,0)
    r = 255
    g = int(255 * (1 - norm))
    b = 0
    return f'#{r:02x}{g:02x}{b:02x}'


def get_depth_color(depth: float) -> str:
    """Return color based on depth range"""
    if depth is None:
        return 'gray'
    if depth < 500:
        return 'blue'       # Too shallow
    elif depth <= 1000:
        return 'green'      # Optimal
    else:
        return 'orange'     # Deep


def create_interactive_map(holes: list[DrillHole], seam_name: str, seam_key: str,
                           counties: list[dict], output_path: str):
    """Create interactive folium map with drill hole data"""
    # Filter valid data
    valid = [h for h in holes if (h.thickness is not None or h.depth is not None)
             and not h.is_outlier]

    if not valid:
        print(f"  No valid data for interactive map: {seam_name}")
        return

    # Center map on data
    center_lat = sum(h.lat for h in valid) / len(valid)
    center_lon = sum(h.lon for h in valid) / len(valid)

    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=9,
                   tiles='cartodbpositron')

    # Add county boundaries
    for county in counties:
        if county['name'].upper() in STUDY_COUNTIES:
            for poly_points in county['polygons']:
                coords = [[p[1], p[0]] for p in poly_points]  # folium uses [lat, lon]
                folium.Polygon(
                    locations=coords,
                    color='black',
                    weight=1,
                    fill=True,
                    fill_color='blue',
                    fill_opacity=0.02,
                    popup=county['name']
                ).add_to(m)

    # Create marker cluster for performance
    marker_cluster = MarkerCluster(name=f'{seam_name} Drill Holes').add_to(m)

    # Add drill hole markers
    max_thick = max((h.thickness for h in valid if h.thickness), default=8)

    for h in valid:
        # Build popup content
        popup_html = f"""
        <b>ID:</b> {h.ids}<br>
        <b>County:</b> {h.county}<br>
        <b>Surface Elev:</b> {h.surfelv:.0f} ft<br>
        """
        if h.thickness is not None:
            popup_html += f"<b>Thickness:</b> {h.thickness:.2f} ft<br>"
        if h.depth is not None:
            popup_html += f"<b>Depth:</b> {h.depth:.0f} ft<br>"
            if 500 <= h.depth <= 1000:
                popup_html += "<b style='color:green'>✓ Optimal CBM depth</b>"

        # Color by thickness if available, else by depth
        if h.thickness is not None:
            color = get_thickness_color(h.thickness, max_thick)
        else:
            color = get_depth_color(h.depth)

        folium.CircleMarker(
            location=[h.lat, h.lon],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=200)
        ).add_to(marker_cluster)

    # Add legend
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
                background-color: white; padding: 10px; border-radius: 5px;
                border: 2px solid gray; font-size: 12px;">
        <b>Thickness</b><br>
        <span style="color: #ffff00;">●</span> Thin (0-2 ft)<br>
        <span style="color: #ffaa00;">●</span> Medium (2-5 ft)<br>
        <span style="color: #ff0000;">●</span> Thick (5+ ft)<br>
        <hr style="margin: 5px 0;">
        <b>Depth (if no thickness)</b><br>
        <span style="color: blue;">●</span> Shallow (<500 ft)<br>
        <span style="color: green;">●</span> Optimal (500-1000 ft)<br>
        <span style="color: orange;">●</span> Deep (>1000 ft)
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Add layer control
    folium.LayerControl().add_to(m)

    # Save
    m.save(output_path)
    print(f"  Saved: {output_path}")


def create_all_seams_map(all_holes: dict[str, list[DrillHole]],
                         counties: list[dict], output_path: str):
    """Create interactive map with all seams as toggleable layers"""
    # Get center from any seam with data
    all_valid = []
    for holes in all_holes.values():
        all_valid.extend([h for h in holes if h.thickness is not None and not h.is_outlier])

    if not all_valid:
        print("  No valid data for all-seams map")
        return

    center_lat = sum(h.lat for h in all_valid) / len(all_valid)
    center_lon = sum(h.lon for h in all_valid) / len(all_valid)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=9,
                   tiles='cartodbpositron')

    # Add county boundaries
    county_group = folium.FeatureGroup(name='County Boundaries')
    for county in counties:
        if county['name'].upper() in STUDY_COUNTIES:
            for poly_points in county['polygons']:
                coords = [[p[1], p[0]] for p in poly_points]
                folium.Polygon(
                    locations=coords,
                    color='black',
                    weight=1,
                    fill=True,
                    fill_color='blue',
                    fill_opacity=0.02,
                ).add_to(county_group)
    county_group.add_to(m)

    # Color scheme per seam
    seam_colors = {
        'herrin': 'red',
        'springfield': 'blue',
        'danville': 'green',
        'colchester': 'purple',
        'seelyville': 'orange',
    }

    # Add each seam as a layer
    for seam_key, holes in all_holes.items():
        valid = [h for h in holes if h.thickness is not None and not h.is_outlier]
        if not valid:
            continue

        seam_name = SEAMS[seam_key]['name']
        color = seam_colors.get(seam_key, 'gray')

        fg = folium.FeatureGroup(name=f'{seam_name} ({len(valid)} pts)')

        for h in valid:
            popup = f"<b>{seam_name}</b><br>Thickness: {h.thickness:.2f} ft"
            if h.depth:
                popup += f"<br>Depth: {h.depth:.0f} ft"

            folium.CircleMarker(
                location=[h.lat, h.lon],
                radius=4,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=popup
            ).add_to(fg)

        fg.add_to(m)

    folium.LayerControl().add_to(m)
    m.save(output_path)
    print(f"  Saved: {output_path}")


def generate_data_quality_report(all_stats: dict, output_path: str):
    """Generate text report of data quality issues"""
    with open(output_path, 'w') as f:
        f.write("COAL DATA QUALITY REPORT\n")
        f.write("=" * 60 + "\n\n")

        for seam_key, stats in all_stats.items():
            seam_name = SEAMS[seam_key]['name']
            f.write(f"{seam_name}\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Total rows:           {stats['total_rows']}\n")
            f.write(f"  Valid coordinates:    {stats['valid_coords']}\n")
            f.write(f"  Has thickness data:   {stats['has_thickness']}\n")
            f.write(f"  Has depth data:       {stats['has_depth']}\n")
            f.write(f"  Outliers (thickness): {stats['outliers_thickness']}\n")
            f.write(f"  Outliers (depth):     {stats['outliers_depth']}\n")
            f.write(f"  Outliers (coords):    {stats['outliers_coords']}\n")
            f.write("\n")

        f.write("=" * 60 + "\n")
        f.write("Outlier criteria (conservative - flagged, not removed):\n")
        f.write(f"  Thickness: < {THICKNESS_MIN} or > {THICKNESS_MAX} ft\n")
        f.write(f"  Depth: < {DEPTH_MIN} or > {DEPTH_MAX} ft\n")
        f.write(f"  Coordinates: outside study area bounds\n")

    print(f"Saved: {output_path}")


def main():
    """Generate all visualizations"""
    print("=" * 60)
    print("GENERATING COAL SEAM VISUALIZATIONS")
    print("=" * 60)

    # Create output directories
    os.makedirs('visualizations/static', exist_ok=True)
    os.makedirs('visualizations/interactive', exist_ok=True)

    # Load county boundaries
    print("\nLoading county boundaries...")
    counties = load_county_boundaries('data/shapefiles/IL_BNDY_County_Py.shp')
    print(f"  Loaded {len(counties)} counties")

    # Load and visualize each seam
    csv_path = 'data/csv/all-coals-study-area-combined.csv'
    all_holes = {}
    all_stats = {}

    for seam_key, seam_config in SEAMS.items():
        seam_name = seam_config['name']
        print(f"\n{seam_name}:")
        print("-" * 40)

        # Load data
        holes, stats = load_drill_holes(csv_path, seam_key)
        all_holes[seam_key] = holes
        all_stats[seam_key] = stats

        print(f"  Loaded {stats['valid_coords']} records")
        print(f"  Thickness data: {stats['has_thickness']}")
        print(f"  Depth data: {stats['has_depth']}")

        # Generate static visualizations
        print("  Generating static maps...")
        create_thickness_map(holes, seam_name, counties,
                            f'visualizations/static/{seam_key}-thickness-map.png')
        create_depth_map(holes, seam_name, counties,
                        f'visualizations/static/{seam_key}-depth-map.png')
        create_histogram(holes, seam_name,
                        f'visualizations/static/{seam_key}-histogram.png')

        # Generate interactive map
        print("  Generating interactive map...")
        create_interactive_map(holes, seam_name, seam_key, counties,
                              f'visualizations/interactive/{seam_key}-map.html')

    # Generate all-seams interactive map
    print("\nGenerating all-seams interactive map...")
    create_all_seams_map(all_holes, counties, 'visualizations/interactive/all-seams-map.html')

    # Generate data quality report
    print("\nGenerating data quality report...")
    generate_data_quality_report(all_stats, 'data-quality-report.txt')

    print("\n" + "=" * 60)
    print("VISUALIZATION COMPLETE")
    print("=" * 60)
    print("\nOutput locations:")
    print("  Static maps:      visualizations/static/")
    print("  Interactive maps: visualizations/interactive/")
    print("  Quality report:   data-quality-report.txt")


if __name__ == '__main__':
    main()
