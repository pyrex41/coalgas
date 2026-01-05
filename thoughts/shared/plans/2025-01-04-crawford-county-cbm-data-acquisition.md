# Crawford County CBM Data Acquisition Plan

## Overview

Systematic extraction and analysis of all available well log and coal resource data for **Crawford County and surrounding counties** (Clark, Lawrence, Jasper, Cumberland, Richland) in Illinois to assess coalbed methane (CBM) potential before committing to a $920K drilling program.

**Primary output format: CSV files with lat/lon coordinates and depth/thickness data.**

## Current State Analysis

### What Exists
Three primary data sources have been verified as accessible:

1. **ILMINES Wiki** (ilmineswiki.web.illinois.edu) - Fully open, no registration
2. **ILOIL Database** (maps.isgs.illinois.edu/iloil) - Free viewing only (skipping paid export)
3. **Illinois Geospatial Data Clearinghouse** - Free GIS downloads

### Key Discoveries - CSV-Friendly Data

| Resource | Status | Format | CSV-Ready? |
|----------|--------|--------|------------|
| **58,000+ Drill Hole Dataset (Major Coals)** | **VERIFIED** | ASCII/Excel | **YES - Primary source** |
| **12,000+ Drill Hole Dataset (Minor Coals)** | **VERIFIED** | ASCII/Excel | **YES - Primary source** |
| Herrin Coal Shapefile | **VERIFIED** | SHP (56 MB) | Convertible via ogr2ogr |
| Springfield Coal Shapefile | **VERIFIED** | SHP (28 MB) | Convertible via ogr2ogr |
| Danville Coal Shapefile | **VERIFIED** | SHP (15 MB) | Convertible via ogr2ogr |
| Colchester Coal Shapefile | **VERIFIED** | SHP (21 MB) | Convertible via ogr2ogr |
| Seelyville Coal Shapefile | **VERIFIED** | SHP (2 MB) | Convertible via ogr2ogr |
| Coal Logs PDFs | **VERIFIED** | PDF | Secondary reference only |
| Mine Maps | **VERIFIED** | PDF | Secondary reference only |

### Critical Data Gap
**No direct gas content measurements exist for Crawford County.** This cannot be resolved through public data - core sampling is required.

## Desired End State

After executing this plan:

1. **CSV files with lat/lon and coal data** for Crawford + 5 surrounding counties:
   - `major-coals-study-area.csv` - Herrin, Springfield, Danville seam data
   - `minor-coals-study-area.csv` - Colchester, Seelyville, etc.
   - `herrin-coal-points.csv` - Shapefile export with depth/thickness
   - `springfield-coal-points.csv` - Shapefile export with depth/thickness
2. **Filtered datasets** clipped to study area (Crawford + adjacent counties)
3. **Summary statistics** for each coal seam by county
4. **Priority target list** in CSV format

### Verification
- [x] All CSV files load correctly in Excel/Python/R
- [x] Lat/lon coordinates in correct range (Lat 38.57-39.49, Lon -88.47 to -87.51)
- [x] Depth values in expected range (actual depths: 100-1320 ft from surface)
- [x] Crawford County has adequate data coverage (414 major coal + 412 minor coal records)

## What We're NOT Doing

- Gas content analysis (requires core samples - Phase 1 drilling)
- Permeability estimation (requires well tests)
- Economic modeling (depends on gas content data)
- Paid ILOIL data export (skipping for now)
- Manual PDF extraction (focusing on CSV-ready data)

---

## Phase 1: Download Drill Hole Datasets (CSV-Ready)

### Overview
Download the ASCII/Excel drill hole datasets - these are the **primary data sources** and already contain lat/lon with depth/thickness data in tabular format.

### Changes Required:

#### 1. Create Local Directory Structure
```bash
mkdir -p data/{downloads,csv,shapefiles,reference-pdfs}
```

#### 2. Download Major Coals Dataset (58,000+ drill holes)
**URL**: `https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/majorcoals-stratdata-ascii.zip`
**Content**: Stratigraphic data for Danville, Herrin, and Springfield Coals
**Format**: ASCII text file AND Excel table with NAD83 lat/lon coordinates

```bash
curl -o data/downloads/majorcoals-stratdata-ascii.zip \
  "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/majorcoals-stratdata-ascii.zip"

unzip -o data/downloads/majorcoals-stratdata-ascii.zip -d data/downloads/majorcoals/
```

#### 3. Download Minor Coals Dataset (12,000+ drill holes)
**URL**: `https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/minorcoals-stratdata-ascii.zip`
**Content**: Data for Jamestown, Colchester, Seelyville, Dekoven, and Davis coals

```bash
curl -o data/downloads/minorcoals-stratdata-ascii.zip \
  "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/minorcoals-stratdata-ascii.zip"

unzip -o data/downloads/minorcoals-stratdata-ascii.zip -d data/downloads/minorcoals/
```

#### 4. Convert to Clean CSV
```bash
# If Excel files, convert using csvkit or Python:
# pip install csvkit
in2csv data/downloads/majorcoals/*.xlsx > data/csv/major-coals-all.csv
in2csv data/downloads/minorcoals/*.xlsx > data/csv/minor-coals-all.csv

# Or if ASCII/text, may already be delimited - inspect and convert:
# head -20 data/downloads/majorcoals/*.txt
```

### Success Criteria:

#### Automated Verification:
- [x] Both ZIP files downloaded successfully
- [x] Files extract without errors
- [x] CSV/Excel files contain lat/lon columns
- [x] Row count matches expected (58,000+ and 12,000+) - Got 58,463 and 12,604

```bash
# Verify downloads
ls -la data/downloads/*.zip
unzip -l data/downloads/majorcoals-stratdata-ascii.zip
wc -l data/csv/major-coals-all.csv
```

#### Manual Verification:
- [ ] Open CSV in Excel - columns are properly delimited
- [ ] Lat/lon values fall within Illinois bounds (~37-42°N, 87-91°W)
- [ ] Depth values present and reasonable

**Implementation Note**: Inspect the file format after download - the ASCII format may be pipe-delimited, tab-delimited, or fixed-width. Adjust conversion accordingly.

---

## Phase 2: Download and Convert Shapefiles to CSV

### Overview
Download coal seam shapefiles and convert to CSV using GDAL's ogr2ogr tool. This provides additional depth/thickness data with point locations.

### Changes Required:

#### 1. Install GDAL (if not present)
```bash
# macOS
brew install gdal

# Ubuntu/Debian
sudo apt-get install gdal-bin

# Verify installation
ogr2ogr --version
```

#### 2. Download Coal Seam Shapefiles
```bash
# Primary target seams
curl -o data/downloads/herrin-coal.zip \
  "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/herrin-coal.zip"

curl -o data/downloads/springfield-coal.zip \
  "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/springfield-coal.zip"

curl -o data/downloads/danville-coal.zip \
  "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/danville-coal.zip"

curl -o data/downloads/colchester-coal.zip \
  "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/colchester-coal.zip"

curl -o data/downloads/seelyville-coal.zip \
  "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/seelyville-coal.zip"

# Reference layers
curl -o data/downloads/counties.zip \
  "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/counties.zip"
```

#### 3. Extract Shapefiles
```bash
cd data/shapefiles
for f in ../downloads/*.zip; do
  unzip -o "$f"
done
cd ../..
```

#### 4. Convert Shapefiles to CSV with Lat/Lon
```bash
# Convert each coal seam shapefile to CSV
# The -lco GEOMETRY=AS_XY adds X,Y columns for point data
# For polygon data, use AS_WKT to get geometry as text

# Herrin Coal (likely has depth, thickness, elevation layers)
ogr2ogr -f CSV data/csv/herrin-coal-depth.csv data/shapefiles/herrin-coal/ \
  -sql "SELECT *, OGR_GEOM_X AS longitude, OGR_GEOM_Y AS latitude FROM \"herrin-depth\"" \
  -lco GEOMETRY=AS_XY 2>/dev/null || \
ogr2ogr -f CSV data/csv/herrin-coal.csv data/shapefiles/herrin-coal/ -lco GEOMETRY=AS_XY

# Springfield Coal
ogr2ogr -f CSV data/csv/springfield-coal.csv data/shapefiles/springfield-coal/ -lco GEOMETRY=AS_XY

# Danville Coal
ogr2ogr -f CSV data/csv/danville-coal.csv data/shapefiles/danville-coal/ -lco GEOMETRY=AS_XY

# Colchester Coal
ogr2ogr -f CSV data/csv/colchester-coal.csv data/shapefiles/colchester-coal/ -lco GEOMETRY=AS_XY

# Seelyville Coal
ogr2ogr -f CSV data/csv/seelyville-coal.csv data/shapefiles/seelyville-coal/ -lco GEOMETRY=AS_XY
```

#### 5. List Available Layers in Each Shapefile
```bash
# Inspect what layers/tables are in each shapefile
ogrinfo data/shapefiles/herrin-coal/
ogrinfo data/shapefiles/springfield-coal/

# Get field names for a specific layer
ogrinfo -so data/shapefiles/herrin-coal/ herrin-depth
```

### Success Criteria:

#### Automated Verification:
- [x] All 6 ZIP files downloaded
- [x] Shapefiles extract with .shp, .shx, .dbf, .prj files
- [x] CSV files created with WKT geometry (polygons, not point data)
- [x] CSV files have depth and/or thickness columns

```bash
# Check CSV headers
head -1 data/csv/herrin-coal.csv
head -1 data/csv/springfield-coal.csv
```

#### Manual Verification:
- [ ] CSV files open in Excel without errors
- [ ] Coordinate columns named appropriately (X/Y or lon/lat)
- [ ] Attribute columns include depth, thickness, elevation as available

---

## Phase 3: Filter Data to Study Area

### Overview
Filter the statewide datasets to Crawford County and surrounding counties: Clark, Lawrence, Jasper, Cumberland, Richland.

### Changes Required:

#### 1. Define Study Area Counties
```
Study area FIPS codes (Illinois = 17):
- Crawford: 17033
- Clark: 17023
- Lawrence: 17101
- Jasper: 17079
- Cumberland: 17035
- Richland: 17159
```

#### 2. Filter Using Python (Recommended)
```python
#!/usr/bin/env python3
"""filter_study_area.py - Filter coal data to Crawford + surrounding counties"""

import pandas as pd

# Study area county names
STUDY_COUNTIES = ['CRAWFORD', 'CLARK', 'LAWRENCE', 'JASPER', 'CUMBERLAND', 'RICHLAND']

# Approximate bounding box for study area (decimal degrees)
# Crawford County center: ~39.0°N, 87.75°W
MIN_LAT, MAX_LAT = 38.5, 39.6
MIN_LON, MAX_LON = -88.3, -87.3

def filter_by_coords(df, lat_col='latitude', lon_col='longitude'):
    """Filter dataframe to study area bounding box"""
    # Handle various column naming conventions
    lat_cols = [c for c in df.columns if 'lat' in c.lower() or c.upper() == 'Y']
    lon_cols = [c for c in df.columns if 'lon' in c.lower() or c.upper() == 'X']

    if lat_cols and lon_cols:
        lat_col = lat_cols[0]
        lon_col = lon_cols[0]

        mask = (
            (df[lat_col] >= MIN_LAT) & (df[lat_col] <= MAX_LAT) &
            (df[lon_col] >= MIN_LON) & (df[lon_col] <= MAX_LON)
        )
        return df[mask].copy()
    else:
        print(f"Warning: Could not identify lat/lon columns in {df.columns.tolist()}")
        return df

def filter_by_county(df, county_col='COUNTY'):
    """Filter dataframe to study area counties"""
    county_cols = [c for c in df.columns if 'county' in c.lower()]
    if county_cols:
        county_col = county_cols[0]
        mask = df[county_col].str.upper().isin(STUDY_COUNTIES)
        return df[mask].copy()
    return df

# Process each CSV
for filename in ['major-coals-all.csv', 'minor-coals-all.csv',
                 'herrin-coal.csv', 'springfield-coal.csv',
                 'danville-coal.csv', 'colchester-coal.csv', 'seelyville-coal.csv']:
    try:
        df = pd.read_csv(f'data/csv/{filename}')
        print(f"\n{filename}: {len(df)} total records")
        print(f"  Columns: {df.columns.tolist()}")

        # Try county filter first, fall back to coordinate filter
        filtered = filter_by_county(df)
        if len(filtered) == len(df):  # County filter didn't work
            filtered = filter_by_coords(df)

        output_name = filename.replace('.csv', '-study-area.csv')
        filtered.to_csv(f'data/csv/{output_name}', index=False)
        print(f"  Filtered to {len(filtered)} records -> {output_name}")

    except Exception as e:
        print(f"  Error processing {filename}: {e}")
```

#### 3. Run Filter Script
```bash
cd /Users/reuben/projects/coalgas
python3 filter_study_area.py
```

#### 4. Alternative: Filter Using csvkit
```bash
# If data has COUNTY column
csvgrep -c COUNTY -r "CRAWFORD|CLARK|LAWRENCE|JASPER|CUMBERLAND|RICHLAND" \
  data/csv/major-coals-all.csv > data/csv/major-coals-study-area.csv

# Count records per county
csvcut -c COUNTY data/csv/major-coals-study-area.csv | sort | uniq -c
```

### Success Criteria:

#### Automated Verification:
- [x] Study area CSV files created
- [x] Record counts reasonable (2,854 major + 2,419 minor = 5,273 total)
- [x] All 6 counties represented in filtered data

```bash
wc -l data/csv/*-study-area.csv
```

#### Manual Verification:
- [x] Spot-check coordinates fall within study area (Lat 38.57-39.49, Lon -88.47 to -87.51)
- [x] Crawford County has data points (414 major + 412 minor)
- [x] No obviously wrong coordinates (0 records with null/zero coords)

---

## Phase 4: Generate Summary Statistics

### Overview
Create summary tables showing coal seam characteristics by county.

### Changes Required:

#### 1. Generate Summary Statistics Script
```python
#!/usr/bin/env python3
"""summarize_coal_data.py - Generate summary statistics for CBM assessment"""

import pandas as pd
import os

def summarize_seam(filepath, seam_name):
    """Generate summary statistics for a coal seam dataset"""
    if not os.path.exists(filepath):
        return None

    df = pd.read_csv(filepath)

    # Identify depth and thickness columns
    depth_cols = [c for c in df.columns if 'depth' in c.lower()]
    thick_cols = [c for c in df.columns if 'thick' in c.lower()]
    county_cols = [c for c in df.columns if 'county' in c.lower()]

    results = {
        'seam': seam_name,
        'total_records': len(df),
        'columns': df.columns.tolist()
    }

    if depth_cols:
        depth_col = depth_cols[0]
        results['depth_min'] = df[depth_col].min()
        results['depth_max'] = df[depth_col].max()
        results['depth_mean'] = df[depth_col].mean()

    if thick_cols:
        thick_col = thick_cols[0]
        results['thickness_min'] = df[thick_col].min()
        results['thickness_max'] = df[thick_col].max()
        results['thickness_mean'] = df[thick_col].mean()

    if county_cols:
        county_col = county_cols[0]
        results['records_by_county'] = df[county_col].value_counts().to_dict()

    return results

# Summarize each seam
seams = [
    ('data/csv/herrin-coal-study-area.csv', 'Herrin (No. 6)'),
    ('data/csv/springfield-coal-study-area.csv', 'Springfield (No. 5)'),
    ('data/csv/danville-coal-study-area.csv', 'Danville'),
    ('data/csv/colchester-coal-study-area.csv', 'Colchester'),
    ('data/csv/seelyville-coal-study-area.csv', 'Seelyville'),
]

print("=" * 60)
print("CRAWFORD COUNTY + SURROUNDING AREA COAL DATA SUMMARY")
print("=" * 60)

for filepath, seam_name in seams:
    stats = summarize_seam(filepath, seam_name)
    if stats:
        print(f"\n{seam_name}")
        print("-" * 40)
        print(f"  Total records: {stats['total_records']}")
        if 'depth_mean' in stats:
            print(f"  Depth range: {stats['depth_min']:.0f} - {stats['depth_max']:.0f} ft")
            print(f"  Depth mean: {stats['depth_mean']:.0f} ft")
        if 'thickness_mean' in stats:
            print(f"  Thickness range: {stats['thickness_min']:.1f} - {stats['thickness_max']:.1f} ft")
            print(f"  Thickness mean: {stats['thickness_mean']:.1f} ft")
        if 'records_by_county' in stats:
            print(f"  Records by county: {stats['records_by_county']}")
    else:
        print(f"\n{seam_name}: No data file found")

# Find locations with >10 ft combined thickness (CBM sweet spots)
print("\n" + "=" * 60)
print("PRIORITY TARGETS (Combined thickness > 10 ft)")
print("=" * 60)
# This would require joining datasets and summing thickness per location
```

#### 2. Create Final Output CSV
```python
# Combine key data into single analysis-ready CSV
combined = pd.DataFrame()
for filepath, seam_name in seams:
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        df['seam'] = seam_name
        combined = pd.concat([combined, df], ignore_index=True)

combined.to_csv('data/csv/all-coals-study-area-combined.csv', index=False)
print(f"\nCombined dataset: {len(combined)} records")
print(f"Saved to: data/csv/all-coals-study-area-combined.csv")
```

### Success Criteria:

#### Automated Verification:
- [x] Summary statistics script runs without errors
- [x] Combined CSV file created (2,854 records)
- [x] Depth values present (note: stored as elevation, not depth from surface)

#### Manual Verification:
- [x] Review summary output for reasonableness (depths 100-1300 ft, thickness 0.5-8 ft)
- [x] Identify any data quality issues (no nulls in key fields, data ranges reasonable)
- [x] Confirm Crawford County has sufficient data density (826 total records)

---

## Phase 5: Download Reference PDFs (Optional)

### Overview
Download PDF maps for visual reference. These are **secondary** to the CSV data but useful for:
- Verifying CSV data against published maps
- Understanding mining history and exclusion zones
- Visualizing depth contours

### Changes Required:

#### 1. Download Mine Maps (for mining exclusion zones)
```bash
mkdir -p data/reference-pdfs/mine-maps

# Crawford County mine map and directory
curl -o data/reference-pdfs/mine-maps/mines-map-crawford.pdf \
  "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/mines-series/mines-maps/pdf-files/mines-map-crawford.pdf"

curl -o data/reference-pdfs/mine-maps/mines-directory-crawford.pdf \
  "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/mines-series/mines-directories/pdf-files/mines-directory-crawford.pdf"

# Quadrangle maps for detail
for quad in birds flat-rock heathsville porterville russellville stoy; do
  curl -o "data/reference-pdfs/mine-maps/${quad}.pdf" \
    "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/topo-mines/${quad}.pdf"
done

# Adjacent county mine maps
for county in clark lawrence jasper cumberland richland; do
  curl -o "data/reference-pdfs/mine-maps/mines-map-${county}.pdf" \
    "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/mines-series/mines-maps/pdf-files/mines-map-${county}.pdf"
done
```

#### 2. Download Depth Maps (for visual reference)
```bash
mkdir -p data/reference-pdfs/depth-maps

for county in crawford clark lawrence jasper cumberland richland; do
  # Herrin depth
  curl -o "data/reference-pdfs/depth-maps/herrin-depth-${county}.pdf" \
    "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/herrin-series/herrin-depth/pdf-files/herrin-depth-${county}.pdf"

  # Springfield depth
  curl -o "data/reference-pdfs/depth-maps/springfield-depth-${county}.pdf" \
    "https://wikiimage.isgs.illinois.edu/ilmines/webfiles/springfield-series/springfield-depth/pdf-files/springfield-depth-${county}.pdf"
done
```

### Success Criteria:

#### Automated Verification:
- [ ] PDF files download without 404 errors
- [ ] File sizes > 0 bytes

#### Manual Verification:
- [ ] PDFs open and display correctly
- [ ] Mine maps show historical mining locations

---

## Final Deliverables

After completing all phases, the `data/` directory will contain:

```
data/
├── csv/
│   ├── major-coals-all.csv              # 58,000+ records statewide
│   ├── major-coals-study-area.csv       # Filtered to 6 counties
│   ├── minor-coals-all.csv              # 12,000+ records statewide
│   ├── minor-coals-study-area.csv       # Filtered to 6 counties
│   ├── herrin-coal-study-area.csv       # Herrin seam points
│   ├── springfield-coal-study-area.csv  # Springfield seam points
│   ├── danville-coal-study-area.csv     # Danville seam points
│   ├── colchester-coal-study-area.csv   # Colchester seam points
│   ├── seelyville-coal-study-area.csv   # Seelyville seam points
│   └── all-coals-study-area-combined.csv # Combined analysis file
├── downloads/                            # Raw downloaded files
├── shapefiles/                           # Extracted shapefiles
└── reference-pdfs/                       # Mine maps and depth maps
    ├── mine-maps/
    └── depth-maps/
```

---

## Testing Strategy

### Data Validation
1. **Coordinate check**: All lat/lon should fall within ~38.5-39.6°N, 87.3-88.3°W
2. **Depth sanity**: Values should be 200-1500 ft for Illinois Basin
3. **Thickness sanity**: Individual seams 0.5-8 ft typical
4. **County coverage**: All 6 study counties should have data points

### Quick Validation Script
```python
import pandas as pd

df = pd.read_csv('data/csv/all-coals-study-area-combined.csv')

# Check coordinate bounds
lat_col = [c for c in df.columns if 'lat' in c.lower()][0]
lon_col = [c for c in df.columns if 'lon' in c.lower()][0]

print(f"Latitude range: {df[lat_col].min():.2f} to {df[lat_col].max():.2f}")
print(f"Longitude range: {df[lon_col].min():.2f} to {df[lon_col].max():.2f}")
print(f"Total records: {len(df)}")
print(f"Seams present: {df['seam'].unique()}")
```

---

## Performance Considerations

- **Total download size**: ~150-200 MB
- **Download time**: 5-15 minutes on typical broadband
- **Processing time**: CSV filtering/conversion < 5 minutes
- **No GIS software required** for CSV workflow (GDAL ogr2ogr is command-line)

---

## References

- ILMINES Wiki: https://ilmineswiki.web.illinois.edu/
- Illinois Coal Resource Shapefiles: https://ilmineswiki.web.illinois.edu/wiki/Illinois_Coal_Resource_Shapefiles
- 58,000+ Drill Hole Dataset: https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/majorcoals-stratdata-ascii.zip
- GDAL ogr2ogr documentation: https://gdal.org/programs/ogr2ogr.html

### Contact Information
- ISGS Coal Section: ilmines@isgs.illinois.edu, 217-244-2414
- ISGS Geological Records Unit: gru@isgs.illinois.edu, 217-333-5109
