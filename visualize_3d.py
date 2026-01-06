#!/usr/bin/env python3
"""visualize_3d.py - Generate 3D coal seam visualizations

Creates:
1. 3D terrain view (pydeck) - Drill holes as columns with seam intersections at depth
2. Cross-section view (Plotly) - Vertical slices through geology along transects
"""

import argparse
import os
from math import sqrt
from typing import Optional

import numpy as np
import pydeck as pdk
import plotly.graph_objects as go

# Import shared utilities from existing module
from visualize_coal_data import (
    DrillHole, SEAMS, STUDY_COUNTIES,
    load_drill_holes, filter_valid, load_county_boundaries
)

# 3D Configuration
DEFAULT_VERTICAL_EXAGGERATION = 10.0
DEFAULT_PITCH = 45  # Camera pitch in degrees
DEFAULT_BEARING = 0  # Camera bearing in degrees

# Seam colors for 3D (RGBA)
SEAM_COLORS_3D = {
    'herrin': [255, 0, 0, 180],      # Red
    'springfield': [0, 0, 255, 180],  # Blue
    'danville': [0, 255, 0, 180],     # Green
    'colchester': [128, 0, 128, 180], # Purple
    'seelyville': [255, 165, 0, 180], # Orange
}

# Plotly colors
SEAM_COLORS_PLOTLY = {
    'herrin': 'red',
    'springfield': 'blue',
    'danville': 'green',
    'colchester': 'purple',
    'seelyville': 'orange',
}


def create_seam_points(holes: list[DrillHole], seam_key: str,
                       vertical_exag: float = DEFAULT_VERTICAL_EXAGGERATION) -> pdk.Layer:
    """Create point layer showing where drill holes intersect a seam"""
    seam = SEAMS[seam_key]
    color = SEAM_COLORS_3D[seam_key]
    seam_name = seam['name']

    data = []
    for h in holes:
        if h.depth is None or h.surfelv is None:
            continue
        if h.is_outlier:
            continue

        # Seam top elevation = surface elevation - depth
        seam_elev = (h.surfelv - h.depth) * vertical_exag

        # Size based on thickness
        size = 100  # default
        if h.thickness is not None and h.thickness > 0:
            size = max(50, min(300, h.thickness * 50))

        data.append({
            'position': [h.lon, h.lat, seam_elev],
            'thickness': h.thickness or 0,
            'depth': h.depth,
            'seam': seam_name,
            'color': color,
            'size': size,
        })

    return pdk.Layer(
        'ScatterplotLayer',
        data=data,
        get_position='position',
        get_fill_color='color',
        get_radius='size',
        radius_scale=1,
        radius_min_pixels=3,
        radius_max_pixels=15,
        pickable=True,
        id=f'seam-{seam_key}',
    )


def create_drillhole_columns(all_holes: dict[str, list[DrillHole]],
                             vertical_exag: float = DEFAULT_VERTICAL_EXAGGERATION) -> pdk.Layer:
    """Create ColumnLayer showing drill holes as vertical lines from surface to deepest seam"""

    # Collect all unique drill hole locations with their data
    hole_data = {}  # keyed by (lon, lat) tuple

    for seam_key, holes in all_holes.items():
        for h in holes:
            if h.surfelv is None or h.is_outlier:
                continue

            key = (round(h.lon, 6), round(h.lat, 6))

            if key not in hole_data:
                hole_data[key] = {
                    'lon': h.lon,
                    'lat': h.lat,
                    'surfelv': h.surfelv,
                    'min_elev': h.surfelv,
                    'seams': [],
                }

            # Track deepest point for this hole
            if h.depth is not None:
                seam_bottom = h.surfelv - h.depth - (h.thickness or 0)
                if seam_bottom < hole_data[key]['min_elev']:
                    hole_data[key]['min_elev'] = seam_bottom

                hole_data[key]['seams'].append({
                    'name': SEAMS[seam_key]['name'],
                    'depth': h.depth,
                    'thickness': h.thickness,
                })

    # Build layer data
    data = []
    for info in hole_data.values():
        # Column goes from min_elev to surface
        column_height = (info['surfelv'] - info['min_elev']) * vertical_exag
        if column_height < 10:  # Skip if no meaningful depth data
            continue

        seam_list = ', '.join(s['name'] for s in info['seams'])

        data.append({
            'position': [info['lon'], info['lat']],
            'elevation': info['min_elev'] * vertical_exag,
            'height': column_height,
            'seams': seam_list,
            'surfelv': info['surfelv'],
        })

    return pdk.Layer(
        'ColumnLayer',
        data=data,
        get_position='position',
        get_elevation='elevation',
        get_fill_color=[100, 100, 100, 120],  # Semi-transparent gray
        radius=30,
        extruded=True,
        pickable=True,
        auto_highlight=True,
        id='drillhole-columns',
    )


def get_legend_html() -> str:
    """Generate HTML legend for 3D view"""
    return '''
    <div id="legend" style="position: fixed; bottom: 20px; left: 20px;
         background: white; padding: 15px; border-radius: 8px;
         box-shadow: 0 2px 6px rgba(0,0,0,0.3); z-index: 1000; font-family: Arial, sans-serif;">
        <h4 style="margin: 0 0 10px 0; font-size: 14px;">Coal Seams</h4>
        <div style="font-size: 12px;">
            <div><span style="color: green;">&#9679;</span> Danville (shallowest)</div>
            <div><span style="color: red;">&#9679;</span> Herrin (No. 6)</div>
            <div><span style="color: blue;">&#9679;</span> Springfield (No. 5)</div>
            <div><span style="color: purple;">&#9679;</span> Colchester</div>
            <div><span style="color: orange;">&#9679;</span> Seelyville (deepest)</div>
        </div>
        <hr style="margin: 10px 0;">
        <div style="font-size: 11px; color: #666;">
            <b>Optimal CBM depth:</b> 500-1000 ft<br>
            <b>Vertical exaggeration:</b> <span id="exag-display">10</span>x<br>
            <b>Gray columns:</b> Drill hole extents
        </div>
    </div>
    '''


def create_3d_terrain_view(all_holes: dict[str, list[DrillHole]],
                           vertical_exag: float = DEFAULT_VERTICAL_EXAGGERATION,
                           output_path: str = 'visualizations/interactive/3d-terrain.html'):
    """Create full 3D terrain view with all seams"""

    # Calculate map center from all data
    all_valid = []
    for holes in all_holes.values():
        all_valid.extend([h for h in holes if h.depth is not None and not h.is_outlier])

    if not all_valid:
        print("  No valid data for 3D view")
        return

    center_lat = sum(h.lat for h in all_valid) / len(all_valid)
    center_lon = sum(h.lon for h in all_valid) / len(all_valid)

    print(f"  Center: ({center_lat:.4f}, {center_lon:.4f}), {len(all_valid)} points")

    # Create layers
    layers = []

    # Add drill hole columns first (rendered at bottom)
    columns_layer = create_drillhole_columns(all_holes, vertical_exag)
    layers.append(columns_layer)

    # Add seam layers (rendered on top of columns)
    for seam_key in SEAMS:
        if seam_key in all_holes:
            layer = create_seam_points(all_holes[seam_key], seam_key, vertical_exag)
            layers.append(layer)

    # Set up view state
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=9,
        pitch=DEFAULT_PITCH,
        bearing=DEFAULT_BEARING,
    )

    # Create deck - using open map style (no Mapbox token needed)
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
        tooltip={
            'html': '<b>Seam:</b> {seam}<br>'
                    '<b>Thickness:</b> {thickness:.1f} ft<br>'
                    '<b>Depth:</b> {depth:.0f} ft',
            'style': {'backgroundColor': 'steelblue', 'color': 'white'}
        }
    )

    # Save to HTML
    deck.to_html(output_path)

    # Add legend to the HTML
    with open(output_path, 'r') as f:
        html = f.read()

    # Insert legend before closing body tag
    legend = get_legend_html()
    html = html.replace('</body>', legend + '</body>')

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"  Saved: {output_path}")


def project_to_transect(holes: list[DrillHole],
                        start: tuple[float, float],
                        end: tuple[float, float],
                        buffer_miles: float = 2.0) -> list[dict]:
    """
    Project drill holes onto a transect line.

    Args:
        holes: List of drill holes
        start: (lon, lat) of transect start
        end: (lon, lat) of transect end
        buffer_miles: Include holes within this distance of transect

    Returns:
        List of dicts with 'distance' (miles along transect) and hole data
    """
    # Convert buffer to approximate degrees (1 degree ~ 69 miles at this latitude)
    buffer_deg = buffer_miles / 69.0

    # Transect vector
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = sqrt(dx**2 + dy**2)

    if length == 0:
        return []

    # Unit vector along transect
    ux, uy = dx / length, dy / length

    projected = []
    for h in holes:
        if h.surfelv is None or h.is_outlier:
            continue

        # Vector from start to hole
        hx = h.lon - start[0]
        hy = h.lat - start[1]

        # Distance along transect (dot product)
        along = hx * ux + hy * uy

        # Distance perpendicular to transect (cross product magnitude)
        perp = abs(hx * uy - hy * ux)

        # Check if within buffer and along transect
        if perp <= buffer_deg and 0 <= along <= length:
            # Convert to miles
            distance_miles = along * 69.0

            projected.append({
                'distance': distance_miles,
                'hole': h,
                'perp_distance': perp * 69.0,
            })

    return sorted(projected, key=lambda x: x['distance'])


def create_cross_section(all_holes: dict[str, list[DrillHole]],
                         start: tuple[float, float],
                         end: tuple[float, float],
                         vertical_exag: float = DEFAULT_VERTICAL_EXAGGERATION,
                         buffer_miles: float = 2.0,
                         output_path: str = 'visualizations/interactive/cross-section.html',
                         title_suffix: str = ''):
    """Create cross-section view along a transect"""

    fig = go.Figure()

    # Collect all projected points
    all_projected = {}
    for seam_key, holes in all_holes.items():
        projected = project_to_transect(holes, start, end, buffer_miles)
        all_projected[seam_key] = projected

    # Find all unique distances for surface profile
    surface_points = []
    for seam_key, projected in all_projected.items():
        for p in projected:
            surface_points.append((p['distance'], p['hole'].surfelv, p['hole']))

    if not surface_points:
        print(f"  No drill holes found along transect")
        return

    # Sort and deduplicate surface points by distance
    surface_points.sort(key=lambda x: x[0])

    # Plot surface profile
    distances = [p[0] for p in surface_points]
    elevations = [p[1] for p in surface_points]

    fig.add_trace(go.Scatter(
        x=distances,
        y=elevations,
        mode='lines',
        name='Land Surface',
        line=dict(color='brown', width=3),
        fill='tozeroy',
        fillcolor='rgba(139, 69, 19, 0.2)',
        hovertemplate='Distance: %{x:.1f} mi<br>Surface Elev: %{y:.0f} ft<extra>Surface</extra>',
    ))

    # Track min/max for axis range
    min_elev = min(elevations)
    max_elev = max(elevations)

    # Plot each seam
    for seam_key in ['danville', 'herrin', 'springfield', 'colchester', 'seelyville']:
        if seam_key not in all_projected:
            continue

        projected = all_projected[seam_key]
        if not projected:
            continue

        seam_name = SEAMS[seam_key]['name']
        color = SEAM_COLORS_PLOTLY[seam_key]
        rgba = SEAM_COLORS_3D[seam_key]

        seam_distances = []
        seam_tops = []
        seam_bottoms = []
        thicknesses = []

        for p in projected:
            h = p['hole']
            if h.depth is None:
                continue

            seam_top = h.surfelv - h.depth
            thick = h.thickness or 0
            seam_bottom = seam_top - thick

            seam_distances.append(p['distance'])
            seam_tops.append(seam_top)
            seam_bottoms.append(seam_bottom)
            thicknesses.append(thick)

            # Track min for axis
            if seam_bottom < min_elev:
                min_elev = seam_bottom

        if not seam_distances:
            continue

        # Sort by distance
        sorted_data = sorted(zip(seam_distances, seam_tops, seam_bottoms, thicknesses))
        seam_distances = [d[0] for d in sorted_data]
        seam_tops = [d[1] for d in sorted_data]
        seam_bottoms = [d[2] for d in sorted_data]
        thicknesses = [d[3] for d in sorted_data]

        # Plot seam as filled area between top and bottom
        # Create polygon by going forward on top, backward on bottom
        x_polygon = seam_distances + seam_distances[::-1]
        y_polygon = seam_tops + seam_bottoms[::-1]

        fig.add_trace(go.Scatter(
            x=x_polygon,
            y=y_polygon,
            fill='toself',
            fillcolor=f'rgba({rgba[0]}, {rgba[1]}, {rgba[2]}, 0.5)',
            line=dict(color=color, width=1),
            name=seam_name,
            hovertemplate=(
                f'<b>{seam_name}</b><br>'
                'Distance: %{x:.1f} mi<br>'
                'Elevation: %{y:.0f} ft<br>'
                '<extra></extra>'
            ),
        ))

        # Also plot individual drill hole points as markers
        fig.add_trace(go.Scatter(
            x=seam_distances,
            y=seam_tops,
            mode='markers',
            name=f'{seam_name} (drill holes)',
            marker=dict(color=color, size=6, symbol='circle'),
            showlegend=False,
            hovertemplate=(
                f'<b>{seam_name}</b><br>'
                'Distance: %{x:.1f} mi<br>'
                'Top Elev: %{y:.0f} ft<br>'
                'Thickness: %{customdata:.1f} ft<extra></extra>'
            ),
            customdata=thicknesses,
        ))

    # Compute transect length in miles
    transect_length = sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2) * 69

    # Configure layout
    elev_range = max_elev - min_elev

    fig.update_layout(
        title=dict(
            text=f'Cross-Section View{title_suffix}<br>'
                 f'<sup>Transect: ({start[0]:.2f}, {start[1]:.2f}) to ({end[0]:.2f}, {end[1]:.2f}) | '
                 f'Buffer: {buffer_miles} mi | Points: {len(surface_points)}</sup>',
            font=dict(size=16),
        ),
        xaxis_title='Distance Along Transect (miles)',
        yaxis_title='Elevation (ft above sea level)',
        hovermode='closest',
        legend=dict(
            x=1.02,
            y=1,
            bgcolor='rgba(255, 255, 255, 0.8)',
        ),
        yaxis=dict(
            range=[min_elev - elev_range * 0.1, max_elev + elev_range * 0.1],
        ),
        xaxis=dict(
            range=[0, transect_length],
        ),
        height=600,
        margin=dict(r=150),
    )

    # Add optimal depth annotation
    fig.add_hline(y=max_elev - 500, line_dash="dash", line_color="green",
                  annotation_text="500 ft depth", annotation_position="right")
    fig.add_hline(y=max_elev - 1000, line_dash="dash", line_color="green",
                  annotation_text="1000 ft depth", annotation_position="right")

    # Save to HTML
    fig.write_html(output_path, include_plotlyjs=True, full_html=True)
    print(f"  Saved: {output_path}")


def get_default_transect() -> tuple[tuple[float, float], tuple[float, float]]:
    """Return default transect line through Crawford County (E-W)"""
    # Crawford County approximate center: 39.0, -87.75
    # Create E-W transect across study area
    start = (-88.2, 39.0)  # West edge
    end = (-87.4, 39.0)    # East edge
    return start, end


def get_ns_transect() -> tuple[tuple[float, float], tuple[float, float]]:
    """Return N-S transect through Crawford County"""
    start = (-87.75, 38.7)  # South
    end = (-87.75, 39.4)    # North
    return start, end


def get_diagonal_transect() -> tuple[tuple[float, float], tuple[float, float]]:
    """Return NW-SE diagonal transect"""
    start = (-88.1, 39.3)  # Northwest
    end = (-87.5, 38.8)    # Southeast
    return start, end


def main():
    parser = argparse.ArgumentParser(
        description='Generate 3D coal seam visualizations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python visualize_3d.py                    # Generate all with defaults
  python visualize_3d.py --exag 20          # 20x vertical exaggeration
  python visualize_3d.py --skip-3d          # Only generate cross-sections
  python visualize_3d.py --transect-start "-88.0,39.0" --transect-end "-87.5,39.0"
        '''
    )
    parser.add_argument('--exag', type=float, default=10.0,
                        help='Vertical exaggeration factor (default: 10)')
    parser.add_argument('--transect-start', type=str, default=None,
                        help='Transect start point as "lon,lat"')
    parser.add_argument('--transect-end', type=str, default=None,
                        help='Transect end point as "lon,lat"')
    parser.add_argument('--buffer', type=float, default=2.0,
                        help='Cross-section buffer distance in miles (default: 2)')
    parser.add_argument('--skip-3d', action='store_true',
                        help='Skip 3D terrain view generation')
    parser.add_argument('--skip-section', action='store_true',
                        help='Skip cross-section generation')

    args = parser.parse_args()

    print("=" * 60)
    print("GENERATING 3D COAL SEAM VISUALIZATIONS")
    print("=" * 60)
    print(f"Vertical exaggeration: {args.exag}x")

    # Create output directory
    os.makedirs('visualizations/interactive', exist_ok=True)

    # Load data
    print("\nLoading drill hole data...")
    csv_path = 'data/csv/all-coals-study-area-combined.csv'
    all_holes = {}

    for seam_key in SEAMS:
        holes, stats = load_drill_holes(csv_path, seam_key)
        all_holes[seam_key] = holes
        print(f"  {SEAMS[seam_key]['name']}: {stats['has_depth']} with depth data")

    # Generate 3D terrain view
    if not args.skip_3d:
        print("\nGenerating 3D terrain view...")
        create_3d_terrain_view(all_holes, args.exag)

    # Generate cross-sections
    if not args.skip_section:
        print("\nGenerating cross-section views...")

        # Parse custom transect points or use defaults
        if args.transect_start and args.transect_end:
            start = tuple(map(float, args.transect_start.split(',')))
            end = tuple(map(float, args.transect_end.split(',')))
            print(f"  Using custom transect: {start} to {end}")
            create_cross_section(all_holes, start, end, args.exag, args.buffer,
                               title_suffix=' (Custom)')
        else:
            # Generate default E-W transect
            start, end = get_default_transect()
            print(f"  E-W transect: {start} to {end}")
            create_cross_section(all_holes, start, end, args.exag, args.buffer,
                               output_path='visualizations/interactive/cross-section.html',
                               title_suffix=' (E-W)')

            # Generate N-S transect
            ns_start, ns_end = get_ns_transect()
            print(f"  N-S transect: {ns_start} to {ns_end}")
            create_cross_section(all_holes, ns_start, ns_end, args.exag, args.buffer,
                               output_path='visualizations/interactive/cross-section-ns.html',
                               title_suffix=' (N-S)')

            # Generate diagonal transect
            diag_start, diag_end = get_diagonal_transect()
            print(f"  NW-SE transect: {diag_start} to {diag_end}")
            create_cross_section(all_holes, diag_start, diag_end, args.exag, args.buffer,
                               output_path='visualizations/interactive/cross-section-nwse.html',
                               title_suffix=' (NW-SE)')

    print("\n" + "=" * 60)
    print("3D VISUALIZATION COMPLETE")
    print("=" * 60)
    print("\nOutput files:")
    if not args.skip_3d:
        print("  3D terrain:       visualizations/interactive/3d-terrain.html")
    if not args.skip_section:
        print("  Cross-section EW: visualizations/interactive/cross-section.html")
        print("  Cross-section NS: visualizations/interactive/cross-section-ns.html")
        print("  Cross-section NW-SE: visualizations/interactive/cross-section-nwse.html")


if __name__ == '__main__':
    main()
