# Data Sources

Complete guide to acquiring all data used in this CBM assessment project.

## Quick Links

| Dataset | Direct Download |
|---------|----------------|
| Major Coals Drill Holes | [majorcoals-stratdata-ascii.zip](https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/majorcoals-stratdata-ascii.zip) |
| Minor Coals Drill Holes | [minorcoals-stratdata-ascii.zip](https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/minorcoals-stratdata-ascii.zip) |
| Coal Resource Shapefiles | [ILMINES Wiki Shapefiles Page](https://ilmineswiki.web.illinois.edu/wiki/Illinois_Coal_Resource_Shapefiles) |

## Data Source: Illinois State Geological Survey (ISGS)

All data in this repository comes from the Illinois State Geological Survey's ILMINES database.

**Main Portal**: https://ilmineswiki.web.illinois.edu/

**Contact**:
- Email: ilmines@isgs.illinois.edu
- Phone: 217-244-2414

---

## 1. Major Coals Drill Hole Data

**URL**: https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/majorcoals-stratdata-ascii.zip

**Contents**: 58,000+ drill hole records with stratigraphic data for:
- Danville Coal (No. 7)
- Herrin Coal (No. 6)
- Springfield Coal (No. 5)

### Download & Extract

```bash
cd data/downloads
curl -O https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/majorcoals-stratdata-ascii.zip
unzip majorcoals-stratdata-ascii.zip -d majorcoals/
```

### Extracted Files

| File | Format | Description |
|------|--------|-------------|
| `coalstrat_major.txt` | Tab-delimited | Main data file |
| `coalstrat_major.xlsx` | Excel | Same data in spreadsheet format |
| `coalstrat_major.html` | HTML | Column definitions and metadata |

### Column Definitions

From `coalstrat_major.html`:

| Column | Description |
|--------|-------------|
| IDS | Unique drill hole identifier |
| COUNTY_NAME | County name (uppercase) |
| LONGITUDE | WGS84 longitude (decimal degrees) |
| LATITUDE | WGS84 latitude (decimal degrees) |
| SURFELV | Surface elevation (ft above sea level) |
| WELL_TYPE | Well classification (Oil and Gas Test, Coal Test, etc.) |
| LOG_TYPE | Type of log data (Electric Log, Survey Core Study, etc.) |
| TOP_DANVILLE | Danville Coal elevation (ft above sea level) |
| THICK_DANVILLE | Danville Coal thickness (ft) |
| TOP_HERRIN | Herrin Coal elevation (ft above sea level) |
| THICK_HERRIN | Herrin Coal thickness (ft) |
| TOP_SPRING | Springfield Coal elevation (ft above sea level) |
| THICK_SPRING | Springfield Coal thickness (ft) |

**Note**: TOP_* values are elevations, not depths. Calculate depth as: `SURFELV - TOP_*`

---

## 2. Minor Coals Drill Hole Data

**URL**: https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/minorcoals-stratdata-ascii.zip

**Contents**: 12,000+ drill hole records with stratigraphic data for:
- Jamestown Coal
- Colchester Coal (No. 2)
- Seelyville Coal
- DeKoven Coal
- Lower DeKoven Coal
- Davis Coal

### Download & Extract

```bash
cd data/downloads
curl -O https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/minorcoals-stratdata-ascii.zip
unzip minorcoals-stratdata-ascii.zip -d minorcoals/
```

### Additional Columns (beyond major coals)

| Column | Description |
|--------|-------------|
| TOP_JTOWN | Jamestown Coal elevation |
| THICK_JTOWN | Jamestown Coal thickness |
| TOP_COLCH | Colchester Coal elevation |
| THICK_COLCH | Colchester Coal thickness |
| TOP_SEELY | Seelyville Coal elevation |
| THICK_SEELY | Seelyville Coal thickness |
| TOP_DEKOVEN | DeKoven Coal elevation |
| THICK_DEKOVEN | DeKoven Coal thickness |
| TOP_LWRDEK | Lower DeKoven Coal elevation |
| THICK_LWRDEK | Lower DeKoven Coal thickness |
| TOP_DAVIS | Davis Coal elevation |
| THICK_DAVIS | Davis Coal thickness |

---

## 3. Coal Seam Shapefiles (Depth & Thickness Contours)

**Source Page**: https://ilmineswiki.web.illinois.edu/wiki/Illinois_Coal_Resource_Shapefiles

These shapefiles contain polygon contours for coal seam depths and thicknesses across Illinois.

### Available Shapefiles

| Coal Seam | Depth Shapefile | Thickness Shapefile |
|-----------|-----------------|---------------------|
| Herrin (No. 6) | IL_Herrin_Coal_Depth_Py | IL_Herrin_Coal_Thickness_Py |
| Springfield (No. 5) | IL_Springfield_Coal_Depth_Py | IL_Springfield_Coal_Thickness_Py |
| Danville (No. 7) | IL_Danville_Coal_Depth_Py | IL_Danville_Coal_Thickness_Py |
| Colchester (No. 2) | IL_Colchester_Coal_Depth_Py | IL_Colchester_Coal_Thickness_Py |
| Seelyville | IL_Seelyville_Coal_Depth_Py | IL_Seelyville_Coal_Thickness_Py |

### Download Links

Each shapefile is available as a ZIP archive. Navigate to the ILMINES Wiki shapefiles page and download each coal seam's depth and thickness files.

Direct pattern: `https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/[FILENAME].zip`

Example for Herrin Coal:
```bash
curl -O https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/IL_Herrin_Coal_Depth_Py.zip
curl -O https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/IL_Herrin_Coal_Thickness_Py.zip
```

### Converting Shapefiles to CSV

Python with `geopandas` or `pyshp`:

```python
import geopandas as gpd

gdf = gpd.read_file("IL_Herrin_Coal_Depth_Py.shp")
gdf.to_csv("herrin-depth.csv", index=False)
```

Or use QGIS/ArcGIS for manual export.

---

## 4. County Boundaries

**URL**: Available from the ILMINES Wiki or Illinois Geospatial Data Clearinghouse

Used for filtering drill hole data to specific study areas.

---

## Processing Steps

After downloading raw data, the following scripts process it:

### Step 1: Convert to CSV

The raw `.txt` files are tab-delimited. Convert to proper CSV:

```python
import csv

with open('coalstrat_major.txt', 'r') as infile:
    reader = csv.reader(infile, delimiter='\t')
    with open('major-coals-all.csv', 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        for row in reader:
            writer.writerow(row)
```

### Step 2: Filter to Study Area

Use `filter_study_area.py` to extract records for the 6-county study area:

```bash
python3 filter_study_area.py
```

This creates `*-study-area.csv` files for the target counties:
- Crawford
- Clark
- Lawrence
- Jasper
- Cumberland
- Richland

### Step 3: Generate Statistics

Use `summarize_coal_data.py` for CBM assessment statistics:

```bash
python3 summarize_coal_data.py
```

---

## Data License

All data is sourced from public Illinois State Geological Survey resources and is available for research and educational purposes.

---

## Example Data

The `examples/` directory contains sample files (50 rows each) for users who want to understand the data format without downloading the full datasets:

| File | Description |
|------|-------------|
| [`major-coals-sample.csv`](examples/major-coals-sample.csv) | Sample major coals drill hole data |
| [`minor-coals-sample.csv`](examples/minor-coals-sample.csv) | Sample minor coals drill hole data |
| [`herrin-depth-sample.csv`](examples/herrin-depth-sample.csv) | Sample Herrin Coal depth contours (WKT polygons) |

---

## Troubleshooting

### Connection Issues

If download links fail:
1. Visit https://ilmineswiki.web.illinois.edu/ directly
2. Navigate to the data section
3. Contact ISGS at ilmines@isgs.illinois.edu

### Missing Data

Some drill holes have blank values for certain coal seams. This is normal - not all drill holes penetrate all coal seams.

### Coordinate System

All coordinates are in WGS84 (EPSG:4326):
- Longitude: Negative values (Western hemisphere)
- Latitude: Positive values (Northern hemisphere)
