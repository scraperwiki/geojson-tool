#!/bin/sh
# Geojson
python geojson.py fixtures/manchester_grit_bins.geojson
python geojson.py fixtures/map.geojson
python geojson.py fixtures/traffic-signs-hansbeke.geojson
python geojson.py fixtures/ashville-crimes.geojson
python geojson.py fixtures/new-zealand-quakes.geojson
# KML
python geojson.py fixtures/KML_Samples.kml # Document at root
python geojson.py fixtures/placemark.kml # features at root
python geojson.py fixtures/CCC_BSC-Feb2013-clipcoast-200m-KML-format.kml # folders at root
python geojson.py fixtures/countries_world.kml # document at root but no folders?