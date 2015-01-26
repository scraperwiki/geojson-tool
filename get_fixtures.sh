#!/bin/sh
# Geojson
curl "http://www.manchester.gov.uk/site/custom_scripts/getdirectorygeo.php?directory=42&category=" -o "fixtures/manchester_grit_bins.geojson"
curl "http://www.paris-streetart.com/test/map.geojson" -o "fixtures/map.geojson"
curl "https://raw.githubusercontent.com/peterdesmet/traffic-signs-hansbeke/master/data/traffic-signs-hansbeke.geojson" -o "fixtures/traffic-signs-hansbeke.geojson"
curl "http://opendataserver.ashevillenc.gov/geoserver/ows?service=WFS&request=GetFeature&srsName=EPSG:4326&typeName=coagis:coa_crime_mapper_apd_locations_view&maxFeatures=10000&outputFormat=json" -o "fixtures/ashville-crimes.geojson"
curl "http://quakesearch.geonet.org.nz/services/1.0.0/geojson?bbox=163.60840,-49.18170,182.98828,-32.28713&startdate=2014-01-01&enddate=2014-08-01" -o "fixtures/new-zealand-quakes.geojson"
# KML
curl "https://dl.dropboxusercontent.com/u/21886071/countries_world.kml" -o "fixtures/countries_world.kml"
curl "https://dl.dropboxusercontent.com/u/21886071/CCC_BSC-Feb2013-clipcoast-200m-KML-format.KML" -o "fixtures/CCC_BSC-Feb2013-clipcoast-200m-KML-format.kml"
curl "https://developers.google.com/kml/documentation/KML_Samples.kml" -o "fixtures/KML_samples.kml"
curl "http://kml-samples.googlecode.com/svn/trunk/kml/Placemark/placemark.kml" -o "fixtures/placemark.kml"