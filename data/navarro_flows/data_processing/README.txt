I did a lot of ETL - spreading, joining, etc, that resulted in a lot of duplicated data, especially geometries
in SQLite/geopackage databases. The data are stored in 7zip files here so that they'll be quite small since they
won't be needed frequently as archives of the process. Extract the files to inspect the source data that went
into the file geodatabase. Workflow was roughly SQLite->Spatialite (joins, recover geometry field)->
geopackage->FGDB. Had to go through geopackage because ArcGIS wouldn't see the geometry on the spatialite version
(probably because of my workflow) and QGIS would see it, but the TimeManager plugin couldn't handle the data,
so I converted to geopackage, sent to ArcGIS, then imported to FGDB, thinking it might like that better.