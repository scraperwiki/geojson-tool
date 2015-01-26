#!/bin/sh
#python geojson.py https://developers.google.com/kml/documentation/KML_Samples.kml # Document at root
#python geojson.py http://kml-samples.googlecode.com/svn/trunk/kml/Placemark/placemark.kml # features at root
python geojson.py fixtures/CCC_BSC-Feb2013-clipcoast-200m-KML-format.kml # folders at root
python geojson.py fixtures/countries_world.kml # document at root but no folders?