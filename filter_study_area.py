#!/usr/bin/env python3
"""filter_study_area.py - Filter coal data to Crawford + surrounding counties (no pandas)"""

import csv
import os
from collections import defaultdict

# Study area county names
STUDY_COUNTIES = {'CRAWFORD', 'CLARK', 'LAWRENCE', 'JASPER', 'CUMBERLAND', 'RICHLAND'}

# Approximate bounding box for study area (decimal degrees)
MIN_LAT, MAX_LAT = 38.5, 39.6
MIN_LON, MAX_LON = -88.3, -87.3

def find_column(headers, patterns):
    """Find column index matching any pattern"""
    for i, h in enumerate(headers):
        h_lower = h.lower()
        for pattern in patterns:
            if pattern in h_lower:
                return i
    return None

def filter_csv(input_path, output_path):
    """Filter CSV to study area by county name or coordinates"""
    with open(input_path, 'r', newline='') as infile:
        reader = csv.reader(infile)
        headers = next(reader)

        # Find relevant columns
        county_idx = find_column(headers, ['county'])
        lat_idx = find_column(headers, ['latitude', 'lat'])
        lon_idx = find_column(headers, ['longitude', 'lon'])

        print(f"  Headers: {headers}")
        print(f"  County col: {headers[county_idx] if county_idx is not None else 'N/A'}")
        print(f"  Lat col: {headers[lat_idx] if lat_idx is not None else 'N/A'}")
        print(f"  Lon col: {headers[lon_idx] if lon_idx is not None else 'N/A'}")

        # Read and filter rows
        filtered_rows = []
        county_counts = defaultdict(int)
        total_rows = 0

        for row in reader:
            total_rows += 1
            keep = False

            # Try county filter first
            if county_idx is not None:
                county = row[county_idx].upper().strip()
                if county in STUDY_COUNTIES:
                    keep = True
                    county_counts[county] += 1

            # Fall back to coordinate filter if no county match
            elif lat_idx is not None and lon_idx is not None:
                try:
                    lat = float(row[lat_idx])
                    lon = float(row[lon_idx])
                    if MIN_LAT <= lat <= MAX_LAT and MIN_LON <= lon <= MAX_LON:
                        keep = True
                except (ValueError, IndexError):
                    pass

            if keep:
                filtered_rows.append(row)

        print(f"  Total rows: {total_rows}")
        print(f"  Filtered rows: {len(filtered_rows)}")

        if county_counts:
            print("  Records by county:")
            for county in sorted(county_counts.keys()):
                print(f"    {county}: {county_counts[county]}")

        # Write filtered output
        with open(output_path, 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(headers)
            writer.writerows(filtered_rows)

        return len(filtered_rows)

# Main execution
print("=" * 60)
print("FILTERING DRILL HOLE DATA TO STUDY AREA")
print("=" * 60)
print(f"Study counties: {sorted(STUDY_COUNTIES)}")
print(f"Bounding box: Lat {MIN_LAT}-{MAX_LAT}, Lon {MIN_LON}-{MAX_LON}")

for filename in ['major-coals-all.csv', 'minor-coals-all.csv']:
    input_path = f'data/csv/{filename}'
    output_name = filename.replace('.csv', '-study-area.csv')
    output_path = f'data/csv/{output_name}'

    print(f"\n{filename}:")
    try:
        count = filter_csv(input_path, output_path)
        print(f"  -> Saved to {output_name}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 60)
print("COMPLETE")
print("=" * 60)
