# Data catalog and processing lineage

`dataset_catalog.csv` is the machine-readable acquisition index. Before a
download becomes usable, add a dataset-specific manifest in this directory
containing: source URL/API request, version/product ID, access date, checksum
when available, license statement, CRS, AOI coverage result, QC result, and
the exact downstream files produced. Do not record credentials here.

Raw data are immutable after download. Each transformation must write a
sidecar provenance file or a row in the dataset manifest with input IDs,
software/environment version, parameters, timestamp, and output ID.
