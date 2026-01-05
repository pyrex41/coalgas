# Handoff: Crawford County CBM Data Acquisition

## Objective

Execute the data acquisition plan to download and process coal resource data for Crawford County and surrounding counties (Clark, Lawrence, Jasper, Cumberland, Richland) in Illinois. The goal is to produce CSV files with lat/lon coordinates and depth/thickness data for CBM (coalbed methane) assessment.

## Key Documents

- **Implementation Plan**: `thoughts/shared/plans/2025-01-04-crawford-county-cbm-data-acquisition.md`
- **SCUD Task Graph**: `.scud/tasks/tasks.scg`

## SCUD Workflow

Use SCUD commands to track progress:

```bash
# View current task status
scud stats

# Get next available task
scud next

# Claim a task before starting
scud next --claim --name "Claude"

# View task details
scud show <task-id>

# Mark task complete
scud set-status <task-id> done

# Commit with task context
scud commit -m "message"
```

## Task Execution Order

Execute tasks following the dependency graph. Parallel tasks can be done together.

### Wave 1 (Start here)
- **Task 1**: Set up directory structure
- **Task 5**: Install GDAL (can run in parallel)

### Wave 2 (After Task 1)
- **Task 2**: Download Major Coals Dataset (58k+ drill holes)
- **Task 3**: Download Minor Coals Dataset (12k+ drill holes)
- **Task 6**: Download coal seam shapefiles
- **Task 10**: Download reference PDFs (optional, low priority)

### Wave 3 (After Wave 2)
- **Task 4**: Convert drill hole datasets to CSV (needs 2, 3)
- **Task 7.1**: Extract ZIPs and inspect shapefile layers (needs 5, 6)

### Wave 4
- **Task 7.2**: Convert shapefiles to CSV (needs 7.1)

### Wave 5
- **Task 8**: Filter datasets to study area (needs 4, 7.2)

### Wave 6
- **Task 9**: Generate summary statistics (needs 8)

## Key URLs

```
# Drill hole datasets (ASCII/Excel - CSV-ready)
https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/majorcoals-stratdata-ascii.zip
https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/minorcoals-stratdata-ascii.zip

# Coal seam shapefiles
https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/herrin-coal.zip
https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/springfield-coal.zip
https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/danville-coal.zip
https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/colchester-coal.zip
https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/seelyville-coal.zip
https://wikiimage.isgs.illinois.edu/ilmines/webfiles/shapefiles/counties.zip
```

## Expected Outputs

```
data/
├── csv/
│   ├── major-coals-all.csv              # 58,000+ records statewide
│   ├── major-coals-study-area.csv       # Filtered to 6 counties
│   ├── minor-coals-all.csv              # 12,000+ records statewide
│   ├── minor-coals-study-area.csv       # Filtered to 6 counties
│   ├── herrin-coal-study-area.csv
│   ├── springfield-coal-study-area.csv
│   ├── danville-coal-study-area.csv
│   ├── colchester-coal-study-area.csv
│   ├── seelyville-coal-study-area.csv
│   └── all-coals-study-area-combined.csv
├── downloads/                            # Raw ZIP files
├── shapefiles/                           # Extracted shapefiles
└── reference-pdfs/                       # Optional mine/depth maps
```

## Study Area Filter Criteria

```python
STUDY_COUNTIES = ['CRAWFORD', 'CLARK', 'LAWRENCE', 'JASPER', 'CUMBERLAND', 'RICHLAND']

# Bounding box fallback (decimal degrees)
MIN_LAT, MAX_LAT = 38.5, 39.6
MIN_LON, MAX_LON = -88.3, -87.3
```

## Success Criteria

1. All CSV files load correctly in Python/Excel
2. Lat/lon coordinates plot within Illinois (37-42°N, 87-91°W)
3. Depth values in range 200-1500 ft
4. Crawford County has adequate data coverage
5. All 6 study counties represented in filtered datasets

## Notes

- **Primary data source**: The 58k+ drill hole ASCII/Excel dataset already has lat/lon - this is the easiest path to CSV
- **Shapefiles**: Require GDAL `ogr2ogr` to convert to CSV - inspect layers first with `ogrinfo`
- **PDFs are optional**: Only needed for visual reference of mining exclusion zones
- **No paid data**: Skip ILOIL bulk export for now

## Commands Reference

```bash
# GDAL install (macOS)
brew install gdal

# Convert shapefile to CSV with coordinates
ogr2ogr -f CSV output.csv input.shp -lco GEOMETRY=AS_XY

# Inspect shapefile layers
ogrinfo input.shp

# Excel to CSV (requires csvkit)
pip install csvkit
in2csv input.xlsx > output.csv
```

---

**Start by running**: `scud next --claim --name "Claude"` to get the first task.
