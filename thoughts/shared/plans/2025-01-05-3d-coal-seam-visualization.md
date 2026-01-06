# 3D Coal Seam Visualization Implementation Plan

## Overview

Extend the existing 2D visualization system to render 3D representations of coal seams below the land surface. This includes:
1. **Full 3D terrain view** with subsurface coal seam layers (pydeck/deck.gl)
2. **Cross-section view** showing vertical slices through the geology (Plotly)

Both outputs will be interactive HTML files, consistent with the existing Folium-based 2D maps.

## Current State Analysis

The existing `visualize_coal_data.py` provides:
- Static PNG maps (matplotlib) for thickness, depth, histograms
- Interactive 2D HTML maps (Folium) for each seam and all-seams combined
- Data loading with outlier detection and validation
- ~2,854 drill hole records with lon/lat, surface elevation, and seam top/thickness data

### Key Data Fields Available:
| Field | Description | Use in 3D |
|-------|-------------|-----------|
| LONGITUDE, LATITUDE | Drill hole location | X, Y position |
| SURFELV | Surface elevation (ft ASL) | Land surface Z |
| TOP_* | Seam top elevation (ft ASL) | Seam surface Z |
| THICK_* | Seam thickness (ft) | Layer depth/color |

## Desired End State

1. **3D Terrain View** (`visualizations/interactive/3d-terrain.html`)
   - Land surface rendered as terrain mesh
   - Each coal seam as a colored subsurface layer
   - Drill holes as vertical columns from surface to deepest seam
   - Configurable vertical exaggeration (default 10x)
   - Layer toggle controls for each seam
   - Hover tooltips with drill hole data

2. **Cross-Section View** (`visualizations/interactive/cross-section.html`)
   - 2D vertical slice along a user-defined transect
   - Surface profile line at top
   - Each seam shown as colored band with thickness
   - Drill holes projected onto transect shown as vertical lines
   - Interactive: hover shows depth/thickness values

### Verification:
- Open both HTML files in browser
- 3D view: rotate/zoom shows seams at correct relative depths
- Cross-section: accurately reflects drill hole data along transect
- All existing 2D visualizations still work

## What We're NOT Doing

- Real-time terrain tile loading (would require API keys, network dependency)
- 3D interpolation/gridding of seam surfaces (just showing drill hole points)
- Underground tunnel/bore visualization
- VR/AR support
- Animation of drilling progression

## Implementation Approach

Use pydeck for the 3D map view (ColumnLayer for drill holes, ScatterplotLayer for seam points at depth) and Plotly for the cross-section view. Both generate standalone HTML files.

---

## Phase 1: Setup and Dependencies

### Overview
Add pydeck and plotly dependencies, create the new visualization module structure.

### Changes Required:

#### 1. Update pyproject.toml
**File**: `pyproject.toml`
**Changes**: Add new dependencies

```toml
[project]
dependencies = [
    "folium>=0.14",
    "matplotlib>=3.7",
    "pyshp>=2.3",
    "pydeck>=0.9",
    "plotly>=5.18",
    "numpy>=1.24",
    "scipy>=1.11",  # For interpolation in cross-section
]
```

#### 2. Create 3D visualization module
**File**: `visualize_3d.py`
**Changes**: New file with configuration constants

```python
#!/usr/bin/env python3
"""visualize_3d.py - Generate 3D coal seam visualizations"""

import pydeck as pdk
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Optional
from dataclasses import dataclass

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
```

### Success Criteria:

#### Automated Verification:
- [ ] Dependencies install: `uv sync`
- [ ] Module imports successfully: `python -c "import visualize_3d"`

#### Manual Verification:
- [ ] No import errors when running the module

---

## Phase 2: 3D Terrain View with Pydeck

### Overview
Create the main 3D visualization showing drill holes as vertical columns and seam intersections as colored points at depth.

### Changes Required:

#### 1. Add drill hole column layer function
**File**: `visualize_3d.py`
**Changes**: Add function to create ColumnLayer for drill holes

```python
def create_drillhole_columns(holes: list[DrillHole],
                              vertical_exag: float = DEFAULT_VERTICAL_EXAGGERATION) -> pdk.Layer:
    """Create ColumnLayer showing drill holes as vertical columns from surface"""
    data = []
    for h in holes:
        if h.surfelv is None:
            continue
        # Find deepest seam for this hole
        min_elev = h.surfelv
        for seam_key in SEAMS:
            top_col = SEAMS[seam_key]['top_col']
            # Would need to access raw data - simplified here

        data.append({
            'position': [h.lon, h.lat],
            'elevation': h.surfelv * vertical_exag,
            'height': 100 * vertical_exag,  # Column height
            'color': [100, 100, 100, 200],  # Gray
        })

    return pdk.Layer(
        'ColumnLayer',
        data=data,
        get_position='position',
        get_elevation='elevation',
        get_fill_color='color',
        radius=50,
        extruded=True,
        pickable=True,
        auto_highlight=True,
    )
```

#### 2. Add seam point layer function
**File**: `visualize_3d.py`
**Changes**: Add function to create ScatterplotLayer for seam intersection points

```python
def create_seam_points(holes: list[DrillHole], seam_key: str,
                        vertical_exag: float = DEFAULT_VERTICAL_EXAGGERATION) -> pdk.Layer:
    """Create point layer showing where drill holes intersect a seam"""
    seam = SEAMS[seam_key]
    color = SEAM_COLORS_3D[seam_key]

    data = []
    for h in holes:
        # Need seam top elevation - this requires loading from raw data
        # For now, use depth from surface
        if h.depth is None or h.thickness is None:
            continue

        seam_elev = h.surfelv - h.depth  # Convert depth to elevation

        data.append({
            'position': [h.lon, h.lat, seam_elev * vertical_exag],
            'thickness': h.thickness,
            'depth': h.depth,
            'color': color,
        })

    return pdk.Layer(
        'ScatterplotLayer',
        data=data,
        get_position='position',
        get_fill_color='color',
        get_radius='thickness',
        radius_scale=100,
        radius_min_pixels=3,
        radius_max_pixels=20,
        pickable=True,
    )
```

#### 3. Add main 3D map creation function
**File**: `visualize_3d.py`
**Changes**: Add function to compose all layers into a pydeck Deck

```python
def create_3d_terrain_view(all_holes: dict[str, list[DrillHole]],
                            vertical_exag: float = DEFAULT_VERTICAL_EXAGGERATION,
                            output_path: str = 'visualizations/interactive/3d-terrain.html'):
    """Create full 3D terrain view with all seams"""

    # Calculate map center from all data
    all_valid = []
    for holes in all_holes.values():
        all_valid.extend([h for h in holes if h.depth is not None])

    if not all_valid:
        print("No valid data for 3D view")
        return

    center_lat = sum(h.lat for h in all_valid) / len(all_valid)
    center_lon = sum(h.lon for h in all_valid) / len(all_valid)
    avg_elev = sum(h.surfelv for h in all_valid if h.surfelv) / len(all_valid)

    # Create layers
    layers = []

    # Add seam layers (rendered first, at bottom)
    for seam_key, holes in all_holes.items():
        layer = create_seam_points(holes, seam_key, vertical_exag)
        layers.append(layer)

    # Set up view state
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=9,
        pitch=DEFAULT_PITCH,
        bearing=DEFAULT_BEARING,
    )

    # Create deck
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style='mapbox://styles/mapbox/light-v10',
        tooltip={
            'html': '<b>Seam:</b> {seam}<br>'
                    '<b>Thickness:</b> {thickness:.1f} ft<br>'
                    '<b>Depth:</b> {depth:.0f} ft',
            'style': {'backgroundColor': 'steelblue', 'color': 'white'}
        }
    )

    # Save to HTML
    deck.to_html(output_path)
    print(f"  Saved: {output_path}")
```

#### 4. Add vertical exaggeration control
**File**: `visualize_3d.py`
**Changes**: Add HTML/JS for exaggeration slider (embedded in output)

```python
def add_exaggeration_control(html_path: str):
    """Add JavaScript slider to control vertical exaggeration"""
    # Read existing HTML
    with open(html_path, 'r') as f:
        html = f.read()

    # Add control panel HTML/JS before closing body tag
    control_html = '''
    <div id="controls" style="position: absolute; top: 10px; left: 10px;
         background: white; padding: 10px; border-radius: 5px; z-index: 1000;">
        <label>Vertical Exaggeration: <span id="exag-value">10</span>x</label><br>
        <input type="range" id="exag-slider" min="1" max="50" value="10"
               oninput="updateExaggeration(this.value)">
    </div>
    <script>
    function updateExaggeration(value) {
        document.getElementById('exag-value').textContent = value;
        // Note: pydeck doesn't support dynamic updates without re-rendering
        // This would require a more complex setup with custom deck.gl
    }
    </script>
    '''

    html = html.replace('</body>', control_html + '</body>')

    with open(html_path, 'w') as f:
        f.write(html)
```

### Success Criteria:

#### Automated Verification:
- [ ] Script runs without errors: `python visualize_3d.py`
- [ ] Output file created: `ls visualizations/interactive/3d-terrain.html`
- [ ] HTML file is valid (non-zero size): `wc -c visualizations/interactive/3d-terrain.html`

#### Manual Verification:
- [ ] 3D view loads in browser and shows terrain
- [ ] Can rotate and zoom the view
- [ ] Different seams visible at different depths
- [ ] Hover tooltips show drill hole data
- [ ] Vertical exaggeration control visible

**Implementation Note**: After completing this phase, pause for manual browser testing before proceeding.

---

## Phase 3: Cross-Section View with Plotly

### Overview
Create a 2D vertical cross-section view showing a slice through the geology along a defined transect line.

### Changes Required:

#### 1. Add transect projection function
**File**: `visualize_3d.py`
**Changes**: Add function to project drill holes onto a transect line

```python
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
    from math import sqrt, atan2, cos, sin, radians

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
        if h.surfelv is None:
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
```

#### 2. Add cross-section plot function
**File**: `visualize_3d.py`
**Changes**: Add function to create Plotly cross-section figure

```python
def create_cross_section(all_holes: dict[str, list[DrillHole]],
                          start: tuple[float, float],
                          end: tuple[float, float],
                          vertical_exag: float = DEFAULT_VERTICAL_EXAGGERATION,
                          buffer_miles: float = 2.0,
                          output_path: str = 'visualizations/interactive/cross-section.html'):
    """Create cross-section view along a transect"""

    fig = go.Figure()

    # Collect all projected points
    all_projected = {}
    for seam_key, holes in all_holes.items():
        projected = project_to_transect(holes, start, end, buffer_miles)
        all_projected[seam_key] = projected

    # Find all unique distances for surface profile
    all_distances = set()
    surface_points = []
    for seam_key, projected in all_projected.items():
        for p in projected:
            all_distances.add(p['distance'])
            surface_points.append((p['distance'], p['hole'].surfelv))

    if not surface_points:
        print(f"No drill holes found along transect")
        return

    # Sort and plot surface
    surface_points.sort()
    fig.add_trace(go.Scatter(
        x=[p[0] for p in surface_points],
        y=[p[1] for p in surface_points],
        mode='lines',
        name='Surface',
        line=dict(color='brown', width=2),
        fill='tozeroy',
        fillcolor='rgba(139, 69, 19, 0.3)',
    ))

    # Plot each seam
    seam_colors_plotly = {
        'herrin': 'red',
        'springfield': 'blue',
        'danville': 'green',
        'colchester': 'purple',
        'seelyville': 'orange',
    }

    for seam_key, projected in all_projected.items():
        if not projected:
            continue

        seam_name = SEAMS[seam_key]['name']
        color = seam_colors_plotly[seam_key]

        distances = []
        tops = []
        bottoms = []
        thicknesses = []

        for p in projected:
            h = p['hole']
            if h.depth is None:
                continue

            seam_top = h.surfelv - h.depth
            seam_bottom = seam_top - (h.thickness or 0)

            distances.append(p['distance'])
            tops.append(seam_top)
            bottoms.append(seam_bottom)
            thicknesses.append(h.thickness or 0)

        if not distances:
            continue

        # Plot seam as filled area between top and bottom
        fig.add_trace(go.Scatter(
            x=distances + distances[::-1],
            y=tops + bottoms[::-1],
            fill='toself',
            fillcolor=f'rgba({",".join(str(c) for c in SEAM_COLORS_3D[seam_key][:3])}, 0.5)',
            line=dict(color=color, width=1),
            name=seam_name,
            hovertemplate=(
                f'<b>{seam_name}</b><br>'
                'Distance: %{x:.1f} mi<br>'
                'Elevation: %{y:.0f} ft<br>'
                '<extra></extra>'
            ),
        ))

    # Configure layout
    fig.update_layout(
        title=f'Cross-Section View (Buffer: {buffer_miles} mi, Exag: {vertical_exag}x)',
        xaxis_title='Distance Along Transect (miles)',
        yaxis_title='Elevation (ft above sea level)',
        hovermode='closest',
        legend=dict(x=1.02, y=1),
        yaxis=dict(scaleanchor=None),  # Don't lock aspect ratio
    )

    # Apply vertical exaggeration by adjusting y-axis range
    all_elevs = [p[1] for p in surface_points]
    for projected in all_projected.values():
        for p in projected:
            if p['hole'].depth:
                all_elevs.append(p['hole'].surfelv - p['hole'].depth)

    if all_elevs:
        min_elev = min(all_elevs)
        max_elev = max(all_elevs)
        range_elev = max_elev - min_elev
        # Exaggerate by reducing the y-axis range display
        fig.update_yaxes(range=[min_elev - range_elev * 0.1, max_elev + range_elev * 0.1])

    # Save to HTML
    fig.write_html(output_path, include_plotlyjs=True, full_html=True)
    print(f"  Saved: {output_path}")
```

#### 3. Add default transect selection
**File**: `visualize_3d.py`
**Changes**: Add function to compute a default N-S or E-W transect through Crawford County

```python
def get_default_transect() -> tuple[tuple[float, float], tuple[float, float]]:
    """Return default transect line through Crawford County (E-W)"""
    # Crawford County approximate center: 39.0, -87.75
    # Create E-W transect across study area
    start = (-88.3, 39.0)  # West edge
    end = (-87.4, 39.0)    # East edge
    return start, end


def get_ns_transect() -> tuple[tuple[float, float], tuple[float, float]]:
    """Return N-S transect through Crawford County"""
    start = (-87.75, 38.6)  # South
    end = (-87.75, 39.5)    # North
    return start, end
```

### Success Criteria:

#### Automated Verification:
- [ ] Script runs without errors: `python visualize_3d.py`
- [ ] Cross-section file created: `ls visualizations/interactive/cross-section.html`
- [ ] HTML contains Plotly chart: `grep -l "plotly" visualizations/interactive/cross-section.html`

#### Manual Verification:
- [ ] Cross-section loads in browser
- [ ] Surface profile visible at top
- [ ] Coal seams visible as colored bands below surface
- [ ] Hover shows elevation and thickness data
- [ ] Seams at correct relative depths (Herrin above Springfield, etc.)

**Implementation Note**: After completing this phase, pause for manual browser testing.

---

## Phase 4: Integration and Main Entry Point

### Overview
Add main() function and CLI arguments for running 3D visualizations.

### Changes Required:

#### 1. Add argument parsing and main function
**File**: `visualize_3d.py`
**Changes**: Add CLI interface

```python
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description='Generate 3D coal seam visualizations')
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

    # Generate cross-section
    if not args.skip_section:
        print("\nGenerating cross-section view...")

        # Parse transect points or use defaults
        if args.transect_start and args.transect_end:
            start = tuple(map(float, args.transect_start.split(',')))
            end = tuple(map(float, args.transect_end.split(',')))
        else:
            start, end = get_default_transect()
            print(f"  Using default E-W transect: {start} to {end}")

        create_cross_section(all_holes, start, end, args.exag, args.buffer)

        # Also create N-S transect
        ns_start, ns_end = get_ns_transect()
        print(f"  Creating N-S transect: {ns_start} to {ns_end}")
        create_cross_section(
            all_holes, ns_start, ns_end, args.exag, args.buffer,
            output_path='visualizations/interactive/cross-section-ns.html'
        )

    print("\n" + "=" * 60)
    print("3D VISUALIZATION COMPLETE")
    print("=" * 60)
    print("\nOutput files:")
    print("  3D terrain:       visualizations/interactive/3d-terrain.html")
    print("  Cross-section EW: visualizations/interactive/cross-section.html")
    print("  Cross-section NS: visualizations/interactive/cross-section-ns.html")


if __name__ == '__main__':
    main()
```

#### 2. Update README with 3D visualization section
**File**: `README.md`
**Changes**: Add 3D visualization documentation

Add after the existing "### Static Plots" section:

```markdown
### 3D Visualizations

Explore coal seams in 3D with depth-accurate subsurface rendering:

| View | Description |
|------|-------------|
| [3D Terrain View](https://pyrex41.github.io/coalgas/visualizations/interactive/3d-terrain.html) | Rotatable 3D view of all seams below surface |
| [Cross-Section (E-W)](https://pyrex41.github.io/coalgas/visualizations/interactive/cross-section.html) | East-West vertical slice through Crawford County |
| [Cross-Section (N-S)](https://pyrex41.github.io/coalgas/visualizations/interactive/cross-section-ns.html) | North-South vertical slice |

To regenerate with custom settings:
```bash
# Default (10x vertical exaggeration)
python visualize_3d.py

# Custom exaggeration
python visualize_3d.py --exag 20

# Custom transect line
python visualize_3d.py --transect-start "-88.0,39.0" --transect-end "-87.5,39.0"
```
```

### Success Criteria:

#### Automated Verification:
- [ ] Script runs with defaults: `python visualize_3d.py`
- [ ] Script runs with custom args: `python visualize_3d.py --exag 20 --skip-section`
- [ ] All output files created: `ls visualizations/interactive/*section*.html visualizations/interactive/3d*.html`
- [ ] README updated: `grep "3D Terrain" README.md`

#### Manual Verification:
- [ ] All 3D visualizations accessible and working
- [ ] CLI help is useful: `python visualize_3d.py --help`
- [ ] Different exaggeration values produce visible differences

---

## Phase 5: Polish and Enhanced Interactivity

### Overview
Add enhanced controls, legends, and polish to the visualizations.

### Changes Required:

#### 1. Add interactive transect selector to cross-section
**File**: `visualize_3d.py`
**Changes**: Create an HTML page with map + cross-section linked

```python
def create_interactive_cross_section_tool(all_holes: dict[str, list[DrillHole]],
                                           output_path: str = 'visualizations/interactive/cross-section-tool.html'):
    """Create interactive tool where user draws transect on map and sees cross-section"""
    # This would be a more complex HTML/JS application
    # For MVP, generate multiple pre-defined transects

    transects = [
        ('E-W through Crawford', (-88.2, 39.0), (-87.5, 39.0)),
        ('N-S through Crawford', (-87.75, 38.7), (-87.75, 39.4)),
        ('NW-SE diagonal', (-88.1, 39.3), (-87.5, 38.8)),
    ]

    # Generate each cross-section
    for name, start, end in transects:
        safe_name = name.lower().replace(' ', '-').replace('through-', '')
        path = f'visualizations/interactive/cross-section-{safe_name}.html'
        create_cross_section(all_holes, start, end, output_path=path)
```

#### 2. Add seam depth legend to 3D view
**File**: `visualize_3d.py`
**Changes**: Enhance legend with typical depth ranges

```python
def get_legend_html() -> str:
    """Generate HTML legend for 3D view"""
    return '''
    <div id="legend" style="position: absolute; bottom: 20px; left: 20px;
         background: white; padding: 15px; border-radius: 8px;
         box-shadow: 0 2px 6px rgba(0,0,0,0.3); z-index: 1000; font-family: sans-serif;">
        <h4 style="margin: 0 0 10px 0;">Coal Seams</h4>
        <div><span style="color: green;">●</span> Danville (shallowest)</div>
        <div><span style="color: red;">●</span> Herrin (No. 6)</div>
        <div><span style="color: blue;">●</span> Springfield (No. 5)</div>
        <div><span style="color: purple;">●</span> Colchester</div>
        <div><span style="color: orange;">●</span> Seelyville (deepest)</div>
        <hr style="margin: 10px 0;">
        <div style="font-size: 12px;">
            <b>Optimal CBM depth:</b> 500-1000 ft<br>
            <b>Vertical exag:</b> <span id="exag-display">10</span>x
        </div>
    </div>
    '''
```

### Success Criteria:

#### Automated Verification:
- [ ] Multiple cross-section files generated
- [ ] Legend HTML embedded in 3D view

#### Manual Verification:
- [ ] Legend is readable and correctly positioned
- [ ] Multiple transect options available
- [ ] Colors in legend match actual visualization

---

## Testing Strategy

### Unit Tests:
- Test `project_to_transect()` with known points
- Test coordinate conversion functions
- Test data loading for 3D attributes

### Integration Tests:
- Verify all output files are valid HTML
- Check that pydeck and plotly libraries render without JS errors

### Manual Testing Steps:
1. Open 3D terrain view, rotate/zoom, verify seams visible
2. Open cross-sections, hover over seams, verify depth values
3. Compare cross-section depths to original 2D maps for consistency
4. Test with different vertical exaggeration values
5. Verify mobile browser compatibility

## Performance Considerations

- ~2,854 drill holes should render smoothly in pydeck
- Consider using `deck.gl` aggregation layers if performance degrades
- Cross-section projections are O(n) and should be fast
- HTML file sizes may be 2-5MB due to embedded Plotly.js

## Dependencies Added

| Package | Version | Purpose |
|---------|---------|---------|
| pydeck | >=0.9 | deck.gl Python bindings for 3D maps |
| plotly | >=5.18 | Interactive cross-section charts |
| scipy | >=1.11 | Optional: interpolation for smoother surfaces |

## References

- [pydeck documentation](https://deckgl.readthedocs.io/en/latest/)
- [deck.gl ColumnLayer](https://deck.gl/docs/api-reference/layers/column-layer)
- [Plotly Python](https://plotly.com/python/)
- Existing implementation: `visualize_coal_data.py`
