# Shadow Ecology Data Management Plan (v1)

**Prepared:** Month 1, Week 1
**PI:** Lilly Jones, PhD · CIRES, CU Boulder

## 1. Data Sources

| Dataset | Source | Access | Format |
|---|---|---|---|
| Sentinel-2 | ESA Copernicus / Microsoft Planetary Computer | Free, open | GeoTIFF (10 m) |
| Landsat | NASA Earthdata | Free, open | GeoTIFF (30 m) |
| PlanetScope | NASA CSDA Program | Free (CSDA allocation), opportunistic | GeoTIFF (3.7 m) |
| NLCD land cover | USGS | Free, open | GeoTIFF (30 m) |
| Groundwater wells / depth-to-water | USGS; Fan et al. 2013 product | Free, open | CSV / GeoTIFF |
| Building footprints | Microsoft / Google | Free, open | GeoPackage |
| Monitoring network records | USGS, NOAA, Tribal environmental agencies | Federal: open; Tribal: by relationship/agreement | CSV / point files |

## 2. Storage and Compute

- **Working storage:** CyVerse Data Store, allocated Month 1
- **Compute:** CyVerse Atmosphere/JupyterHub (GPU for CNN training); fallback CU Research Computing (Alpine/Blanca) or Colab Pro if allocation is delayed
- **Version control:** GitHub repository (code, documentation, small reference files only: no large rasters committed to git)

## 3. Data Organization

```
data/
  raw/          untouched downloads, organized by source
  processed/    reprojected, clipped, QC'd layers ready for modeling
  training/     training point samples, spatial CV fold assignments
results/
  residuals/    GeoTIFF residual fields, by architecture and metric
  stats/        Moran's I, LISA, null model outputs (CSV/notebook)
```

## 4. Naming and Metadata Conventions

- All raster outputs: GeoTIFF with CRS and geotransform matching the Sentinel-2 stack
- Band order and value definitions documented in a per-directory README
- File naming: `{region}_{sensor}_{date}_{product}.tif` (ex. `riograndebasin_s2_2026-07_composite.tif`)

## 5. Tribal Data Governance

Monitoring data and contextual information sourced through Tribal environmental agency relationships are subject to the data use terms agreed with each partner (see `docs/data_use_statement.md`). Federal open datasets (USGS, NOAA, NLCD) are used under their standard public-domain terms; Tribal-sourced data is not treated the same way and is not redistributed without explicit agreement. Phase 3 results involving Tribal lands are shared back with the relevant Tribal environmental programs per the project workplan.

## 6. Preservation and Sharing

- Code and documentation: public GitHub repository
- Federally-sourced derived data products (residual fields, statistical outputs not involving Tribal-sourced inputs): archived to a public repository (e.g., CyVerse Data Commons) at project completion
- Tribal-sourced data and any products derived jointly with Tribal partners: sharing and archiving terms determined in consultation with those partners, not unilaterally by the PI

## 7. Revision History

| Version | Date | Change |
|---|---|---|
| v1 | Month 1, Week 1 | Initial draft |
