#!/usr/bin/env python

from __future__ import print_function
import json
import os
import sys

import requests
import logging
import lxml
logging.basicConfig()

from fastkml import kml

import scraperwiki

def main(argv=None):
    if argv is None:
        argv = sys.argv
    arg = argv[1:]

    if len(arg) > 0:
        # Developers can supply URL as an argument...
        url = arg[0]
    else:
        # ... but normally the URL comes from the allSettings.json file
        with open(os.path.expanduser("~/allSettings.json")) as settings:
            url = json.load(settings)['source-url']

    return convert_one(url)

def convert_one(url):
    """
    Convert a single URL.
    """
    response = requests.get(url)

    try:
        j = json.loads(response.content)
        parse_geojson(j)
    except:
        parse_kml(response.content)

def parse_geojson(j):
    
    # Avoid using response.json() because it assumes ISO-8859-1 instead of
    # utf-8 when the server doesn't say. And as per
    # https://tools.ietf.org/html/rfc7159 JSON will most likely be
    # encoded in utf-8. Passing the raw (byte) string to json.loads()
    # does the Right Thing.
    
    scraperwiki.sql.execute("DROP TABLE IF EXISTS feature")
    scraperwiki.sql.execute("DROP TABLE IF EXISTS polygon")

    features = []
    polygons = []
    for feature_index, feature in enumerate(j['features'], start=1):
        # The row we are going to add;
        # it's the properties of the feature.
        row = feature['properties']
        print(row)
        # Make sure we have a common key across tables
        row['feature_index'] = feature_index
        # Add feature.id to the row if there is one.
        if 'id' in feature:
            # Avoid issue 3 which is when there is already a
            # property called "id" but with a different case.
            # https://github.com/scraperwiki/geojson-tool/issues/3
            # (we do not fix the general version of this case issue)
            keys = set(k.lower() for k in row.keys())
            if 'id' not in keys:
                row['id'] = feature['id']
        geometry = feature.get('geometry')
        if not geometry:
            continue
        if geometry.get('type') == "Point":
            add_point(row, geometry)
        if geometry.get('type') == "Polygon":
            add_polygon(feature_index, polygons, geometry['coordinates'])
        if geometry.get('type') == "MultiPolygon":
            add_multi_polygon(feature_index, polygons, geometry)

        features.append(row)

    scraperwiki.sql.save([], features, table_name="feature")
    scraperwiki.sql.save([], polygons, table_name="polygon")

def parse_kml(content):
    scraperwiki.sql.execute("DROP TABLE IF EXISTS feature")
    scraperwiki.sql.execute("DROP TABLE IF EXISTS polygon")

    features = []
    polygons = []

    k = kml.KML()
    k.from_string(content)
    #print(content)
    kml_features = list(k.features())
    feature_list = list(kml_features[0].features())
    attributes = [a for a in dir(feature_list[0]) if a[0] is not "_" ]
    #print(attributes)

    for feature_index, feature in enumerate(feature_list, start=1):
        #print(feature.to_string())
         # The row we are going to add;
        # it's the properties of the feature.
        row = {}
        for a in attributes:
            #print(a)
            try:
                value = getattr(feature, a)
                if type(value) in [str, int]:
                    row[a] = value
            except AttributeError:
                pass

        # Make sure we have a common key across tables
        row['feature_index'] = feature_index
        # print(row)
        # Add feature.id to the row if there is one.

        geometry = feature.geometry
        if not geometry:
            continue
        if geometry.geom_type == "Point":
            add_kml_point(row, geometry)
        if geometry.geom_type == "Polygon":
            add_polygon(feature_index, polygons, [geometry.exterior.coords])

        features.append(row)

    scraperwiki.sql.save([], features, table_name="feature")
    scraperwiki.sql.save([], polygons, table_name="polygon")

def add_kml_point(row, geometry):
    pass

def add_point(row, geometry):
    """
    Extract the data for a point from the geometry dict, and
    modify the `row` dict accordingly.
    """

    assert geometry.get('type') == "Point"

    coordinates = geometry['coordinates']
    longitude, latitude = coordinates[:2]
    if len(coordinates) > 2:
        row['elevation'] = coordinates[2]
    row['longitude'] = longitude
    row['latitude'] = latitude
    return

def add_polygon(feature_index, polygons, coordinates):
    """
    Extract the data for a polygon from the geometry dict, and
    add several rows to the `polygons` list.
    """
    
    for polygon_index, points in enumerate(coordinates, start=1):
        for point_index, point in enumerate(points, start=1):
            row = dict(feature_index=feature_index,
              polygon_index=polygon_index,
              point_index=point_index,
              longitude=point[0],
              latitude=point[1])
            polygons.append(row)
    return

def add_multi_polygon(feature_index, polygons, geometry):
    """
    Extract the data for multiple polygons from the geometry dict, and
    add several rows to the `polygons` list.
    """

    assert geometry.get('type') == "MultiPolygon"

    coordinates = geometry['coordinates']
    for polygon_index, points in enumerate(coordinates, start=1):
        for point_index, point in enumerate(points[0], start=1):
            row = dict(feature_index=feature_index,
              polygon_index=polygon_index,
              point_index=point_index,
              longitude=point[0],
              latitude=point[1])
            polygons.append(row)
    return


if __name__ == '__main__':
    main()
