#!/usr/bin/env python

from __future__ import print_function
import json
import os
import sys

import requests
import logging
import lxml
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig()

from fastkml import kml

import scraperwiki

# Examples
# python geojson.py https://developers.google.com/kml/documentation/KML_Samples.kml # Document at root
# python geojson.py http://kml-samples.googlecode.com/svn/trunk/kml/Placemark/placemark.kml # features at root
# python geojson.py https://dl.dropboxusercontent.com/u/21886071/CCC_BSC%20Feb2013%20%28clipcoast%20200m%29%20KML%20format.KML # folders at root
# python geojson.py https://dl.dropboxusercontent.com/u/21886071/countries_world.kml # document at root but no folders?
# Minimal test for ipython:
"""
import requests
from fastkml import kml
url = "https://dl.dropboxusercontent.com/u/21886071/countries_world.kml"
response = requests.get(url)
k = kml.KML()
k.from_string(response.content)
"""

# top_level = list(k.features())
# top_level[0]
# <fastkml.kml.Document at 0x23f5610>
# top_level[0].name
# folders = list(top_level[0].features())
# feature_list = list(folders[0].features())
#


def main(argv=None):
    if argv is None:
        argv = sys.argv
    arg = argv[1:]

    if len(arg) > 0:
        # Developers can supply URL as an argument...
        url = arg[0]
        logging.basicConfig(level=logging.DEBUG)
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

    scraperwiki.sql.execute("DROP TABLE IF EXISTS feature")
    scraperwiki.sql.execute("DROP TABLE IF EXISTS polygon")

    features = []
    polygons = []

    try:
        j = json.loads(response.content)
        features, polygons = parse_geojson(j, features, polygons)
    except:
        k = kml.KML()
        k.from_string(response.content)
        features, polygons = parse_kml(k, features, polygons)

    logging.debug(("Writing {} features, and {} polygons to db".format(
        len(features), len(polygons))))
    scraperwiki.sql.save([], features, table_name="feature")
    scraperwiki.sql.save([], polygons, table_name="polygon")


def parse_geojson(j, features, polygons):

    # Avoid using response.json() because it assumes ISO-8859-1 instead of
    # utf-8 when the server doesn't say. And as per
    # https://tools.ietf.org/html/rfc7159 JSON will most likely be
    # encoded in utf-8. Passing the raw (byte) string to json.loads()
    # does the Right Thing.

    for feature_index, feature in enumerate(j['features'], start=1):
        # The row we are going to add;
        # it's the properties of the feature.
        row = feature['properties']
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
            add_point(row, geometry["coordinates"])
        if geometry.get('type') == "Polygon":
            add_polygon(feature_index, polygons, geometry['coordinates'])
        if geometry.get('type') == "MultiPolygon":
            add_multi_polygon(feature_index, polygons, geometry)

        features.append(row)

    return features, polygons


def parse_kml(k, features, polygons):

    # KML files can have features, folders or document at the root level
    folders = []
    folder_names = []

    folders, folder_names = walk_kml_tree(k, folders, folder_names)

    # We need to have a list of folders at this point, each containing a list
    # of features
    for i, folder in enumerate(folders, start=0):
        # get folder name
        # if we have a placemark or a folder at top level we might want to fake
        # the folder_name
        folder_name = folder_names[i]
        for feature_index, feature in enumerate(folder, start=1):
            attributes = [a for a in dir(feature) if a[0] is not "_"]
            # The row we are going to add;
            # it's the properties of the feature.
            row = {}
            for a in attributes:
                try:
                    value = getattr(feature, a)
                    if type(value) in [str, int]:
                        row[a] = value
                except AttributeError:
                    pass

            # Make sure we have a common key across tables
            row['folder_name'] = folder_name
            row['feature_index'] = feature_index
            try:
                geometry = feature.geometry
                row, features, polygons = add_kml_geometry(
                    features, row, polygons, feature_index, folder_name, geometry)
            except Exception as e:
                logging.debug("Exception thrown: {}".format(e.message))
            # pass

    return features, polygons


def add_kml_geometry(features, row, polygons, feature_index, folder_name, geometry):
    if not geometry:
        return features, polygons
    if geometry.geom_type == "Point":
        add_point(row, geometry.coords[0])
    if geometry.geom_type == "Polygon":
        add_polygon(
            folder_name, feature_index, polygons, [geometry.exterior.coords])
    if geometry.geom_type == "MultiPolygon":
        kml_polygons = [p.exterior.coords for p in geometry.geoms]
        add_polygon(
            folder_name, feature_index, polygons, kml_polygons)
    if geometry.geom_type == "GeometryCollection":
        for g in list(geometry.geoms):
            row, features, polygons = add_kml_geometry(
                features, row, polygons, feature_index, folder_name, g)

    features.append(row)

    return row, features, polygons


def walk_kml_tree(k, folders, folder_names):
    if type(k) is kml.Placemark:
        # Feature at top level
        folders.append([k])
        if len(folder_names) == 0:
            folder_names = ["Feature"]
        else:
            folder_names.append(folder_names[-1] + "-Feature")
        return folders, folder_names

    kml_features = list(k.features())
    if len(kml_features) == 0:
        return folders, folder_names

    if type(kml_features[0]) is kml.Document:
        # Handle a Document
        assert len(kml_features) == 1
        if kml_features[0].name is not None:
            folder_names.append(kml_features[0].name)
        else:
            folder_names.append("Document")

        for f in list(kml_features[0].features()):
            folders, folder_names = walk_kml_tree(f, folders, folder_names)
    elif type(kml_features[0]) is kml.Folder:
        # Folder at top level
        feature_list = list(kml_features[0].features())
        folders.append(feature_list)
        if len(folder_names) == 0:
            folder_names = ["Folder"]  # kml_features[0].name
        else:
            # kml_features[0].name)
            folder_names.append(folder_names[-1] + "Folder")
    elif type(kml_features[0]) is kml.Placemark:
        # Feature at top level
        feature_list = kml_features
        folders.append(feature_list)
        if len(folder_names) == 0:
            folder_names = ["Feature"]
        else:
            folder_names.append(folder_names[-1] + "-Feature")

    return folders, folder_names


def add_point(row, coordinates):
    """
    Extract the data for a point from the geometry dict, and
    modify the `row` dict accordingly.
    """

    longitude, latitude = coordinates[:2]
    if len(coordinates) > 2:
        row['elevation'] = coordinates[2]
    row['longitude'] = longitude
    row['latitude'] = latitude
    return


def add_polygon(folder_name, feature_index, polygons, coordinates):
    """
    Extract the data for a polygon from the geometry dict, and
    add several rows to the `polygons` list.
    """

    for polygon_index, points in enumerate(coordinates, start=1):
        for point_index, point in enumerate(points, start=1):
            row = dict(folder_name=folder_name,
                       feature_index=feature_index,
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
