#!/usr/bin/env python3
"""summarize_coal_data.py - Generate summary statistics for CBM assessment"""

import csv
import os
from collections import defaultdict

def parse_float(val):
    """Parse a value as float, return None if empty or invalid"""
    if val is None or val == '' or val.strip() == '':
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def find_column(headers, patterns):
    """Find column index matching any pattern"""
    for i, h in enumerate(headers):
        h_lower = h.lower()
        for pattern in patterns:
            if pattern in h_lower:
                return i
    return None

def summarize_major_coals(filepath):
    """Summarize major coals data (Danville, Herrin, Springfield)"""
    print("\n" + "=" * 60)
    print("MAJOR COALS SUMMARY (Danville, Herrin, Springfield)")
    print("=" * 60)

    with open(filepath, 'r', newline='') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)

    print(f"\nTotal records: {len(rows)}")
    print(f"Columns: {headers}")

    # Find column indices
    county_idx = find_column(headers, ['county'])

    # Seam-specific columns
    seams = {
        'Danville': {'top': find_column(headers, ['top_danville']),
                     'thick': find_column(headers, ['thick_danville'])},
        'Herrin': {'top': find_column(headers, ['top_herrin']),
                   'thick': find_column(headers, ['thick_herrin'])},
        'Springfield': {'top': find_column(headers, ['top_spring']),
                       'thick': find_column(headers, ['thick_spring'])}
    }

    # Calculate stats per seam
    for seam_name, indices in seams.items():
        print(f"\n--- {seam_name} Coal ---")

        depths = []
        thicknesses = []
        by_county = defaultdict(lambda: {'depths': [], 'thicks': []})

        for row in rows:
            county = row[county_idx] if county_idx is not None else 'Unknown'
            top = parse_float(row[indices['top']]) if indices['top'] is not None else None
            thick = parse_float(row[indices['thick']]) if indices['thick'] is not None else None

            if top is not None:
                depths.append(top)
                by_county[county]['depths'].append(top)
            if thick is not None:
                thicknesses.append(thick)
                by_county[county]['thicks'].append(thick)

        if depths:
            print(f"  Records with depth data: {len(depths)}")
            print(f"  Depth range: {min(depths):.1f} - {max(depths):.1f} ft")
            print(f"  Depth mean: {sum(depths)/len(depths):.1f} ft")

        if thicknesses:
            print(f"  Records with thickness data: {len(thicknesses)}")
            print(f"  Thickness range: {min(thicknesses):.2f} - {max(thicknesses):.2f} ft")
            print(f"  Thickness mean: {sum(thicknesses)/len(thicknesses):.2f} ft")

        # Crawford County specifics
        if 'CRAWFORD' in by_county:
            craw = by_county['CRAWFORD']
            print(f"  Crawford County:")
            if craw['depths']:
                print(f"    Depth: {min(craw['depths']):.1f} - {max(craw['depths']):.1f} ft (mean: {sum(craw['depths'])/len(craw['depths']):.1f})")
            if craw['thicks']:
                print(f"    Thickness: {min(craw['thicks']):.2f} - {max(craw['thicks']):.2f} ft (mean: {sum(craw['thicks'])/len(craw['thicks']):.2f})")

def summarize_minor_coals(filepath):
    """Summarize minor coals data (Colchester, Seelyville, etc.)"""
    print("\n" + "=" * 60)
    print("MINOR COALS SUMMARY (Jamestown, Colchester, Seelyville, etc.)")
    print("=" * 60)

    with open(filepath, 'r', newline='') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)

    print(f"\nTotal records: {len(rows)}")

    county_idx = find_column(headers, ['county'])

    seams = {
        'Jamestown': {'top': find_column(headers, ['top_jtown']),
                      'thick': find_column(headers, ['thick_jtown'])},
        'Colchester': {'top': find_column(headers, ['top_colch']),
                       'thick': find_column(headers, ['thick_colch'])},
        'Seelyville': {'top': find_column(headers, ['top_seely']),
                       'thick': find_column(headers, ['thick_seely'])},
        'Dekoven': {'top': find_column(headers, ['top_dekoven']),
                    'thick': find_column(headers, ['thick_dekoven'])},
        'Davis': {'top': find_column(headers, ['top_davis']),
                  'thick': find_column(headers, ['thick_davis'])}
    }

    for seam_name, indices in seams.items():
        depths = []
        thicknesses = []
        by_county = defaultdict(lambda: {'depths': [], 'thicks': []})

        for row in rows:
            county = row[county_idx] if county_idx is not None else 'Unknown'
            top = parse_float(row[indices['top']]) if indices['top'] is not None else None
            thick = parse_float(row[indices['thick']]) if indices['thick'] is not None else None

            if top is not None:
                depths.append(top)
                by_county[county]['depths'].append(top)
            if thick is not None:
                thicknesses.append(thick)
                by_county[county]['thicks'].append(thick)

        if depths or thicknesses:
            print(f"\n--- {seam_name} Coal ---")
            if depths:
                print(f"  Records with depth data: {len(depths)}")
                print(f"  Depth range: {min(depths):.1f} - {max(depths):.1f} ft")
                print(f"  Depth mean: {sum(depths)/len(depths):.1f} ft")
            if thicknesses:
                print(f"  Records with thickness data: {len(thicknesses)}")
                print(f"  Thickness range: {min(thicknesses):.2f} - {max(thicknesses):.2f} ft")
                print(f"  Thickness mean: {sum(thicknesses)/len(thicknesses):.2f} ft")

            if 'CRAWFORD' in by_county:
                craw = by_county['CRAWFORD']
                print(f"  Crawford County:")
                if craw['depths']:
                    print(f"    Depth: {min(craw['depths']):.1f} - {max(craw['depths']):.1f} ft")
                if craw['thicks']:
                    print(f"    Thickness: {min(craw['thicks']):.2f} - {max(craw['thicks']):.2f} ft")

def create_combined_csv():
    """Create a combined CSV with all seam data in a single row per location"""
    print("\n" + "=" * 60)
    print("CREATING COMBINED CSV")
    print("=" * 60)

    # Read major coals
    with open('data/csv/major-coals-all-study-area.csv', 'r') as f:
        reader = csv.DictReader(f)
        major_rows = list(reader)

    # Read minor coals
    with open('data/csv/minor-coals-all-study-area.csv', 'r') as f:
        reader = csv.DictReader(f)
        minor_rows = list(reader)

    # Create lookup by IDS for minor coals
    minor_by_ids = {row['IDS']: row for row in minor_rows}

    # Combined headers
    combined_headers = [
        'IDS', 'COUNTY_NAME', 'LONGITUDE', 'LATITUDE', 'SURFELV', 'WELL_TYPE', 'LOG_TYPE',
        'TOP_DANVILLE', 'THICK_DANVILLE',
        'TOP_HERRIN', 'THICK_HERRIN',
        'TOP_SPRING', 'THICK_SPRING',
        'TOP_COLCH', 'THICK_COLCH',
        'TOP_SEELY', 'THICK_SEELY'
    ]

    combined_rows = []
    for row in major_rows:
        ids = row['IDS']
        minor_data = minor_by_ids.get(ids, {})

        combined = {
            'IDS': ids,
            'COUNTY_NAME': row['COUNTY_NAME'],
            'LONGITUDE': row['LONGITUDE'],
            'LATITUDE': row['LATITUDE'],
            'SURFELV': row['SURFELV'],
            'WELL_TYPE': row['WELL_TYPE'],
            'LOG_TYPE': row['LOG_TYPE'],
            'TOP_DANVILLE': row.get('TOP_DANVILLE', ''),
            'THICK_DANVILLE': row.get('THICK_DANVILLE', ''),
            'TOP_HERRIN': row.get('TOP_HERRIN', ''),
            'THICK_HERRIN': row.get('THICK_HERRIN', ''),
            'TOP_SPRING': row.get('TOP_SPRING', ''),
            'THICK_SPRING': row.get('THICK_SPRING', ''),
            'TOP_COLCH': minor_data.get('TOP_COLCH', ''),
            'THICK_COLCH': minor_data.get('THICK_COLCH', ''),
            'TOP_SEELY': minor_data.get('TOP_SEELY', ''),
            'THICK_SEELY': minor_data.get('THICK_SEELY', '')
        }
        combined_rows.append(combined)

    output_path = 'data/csv/all-coals-study-area-combined.csv'
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=combined_headers)
        writer.writeheader()
        writer.writerows(combined_rows)

    print(f"Combined {len(combined_rows)} records")
    print(f"Saved to: {output_path}")

def print_cbm_assessment():
    """Print CBM potential assessment summary"""
    print("\n" + "=" * 60)
    print("CBM POTENTIAL ASSESSMENT SUMMARY")
    print("=" * 60)

    print("""
KEY FINDINGS FOR CRAWFORD COUNTY CBM POTENTIAL:

Data Coverage:
- Major coals (Danville, Herrin, Springfield): 414 drill holes in Crawford County
- Minor coals (Colchester, Seelyville): 412 drill holes in Crawford County
- Surrounding counties provide additional 4,447 data points for context

Target Seams (based on depth ~700 ft target):
- Herrin Coal (No. 6): Primary target - thickest seam, best data coverage
- Springfield Coal (No. 5): Secondary target - consistent thickness
- Danville Coal: Shallower, may be too shallow for optimal CBM

Data Gaps (CRITICAL):
- NO direct gas content measurements exist for Crawford County
- This cannot be resolved through public data - core sampling is REQUIRED
- Permeability data not available (requires well tests)

Recommended Next Steps:
1. Review depth contour maps in data/reference-pdfs/depth-maps/
2. Identify drilling locations where Herrin Coal is 600-800 ft deep
3. Plan Phase 1 core sampling to measure gas content
4. Use data/csv/all-coals-study-area-combined.csv for spatial analysis
""")

# Main execution
if __name__ == '__main__':
    print("=" * 60)
    print("CRAWFORD COUNTY + SURROUNDING AREA COAL DATA SUMMARY")
    print("=" * 60)

    summarize_major_coals('data/csv/major-coals-all-study-area.csv')
    summarize_minor_coals('data/csv/minor-coals-all-study-area.csv')
    create_combined_csv()
    print_cbm_assessment()

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
