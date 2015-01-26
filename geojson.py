#!/usr/bin/env python

from __future__ import print_function
import json
import os
import sys
import time

import requests
import logging
import lxml

from fastkml import kml

import scraperwiki

global_polygon_index = 0


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
        logging.basicConfig()

    t0 = time.time()
    logging.debug("Processing {}".format(url))
    convert_one(url)
    t1 = time.time()
    logging.debug(
        "Total time for processing {0} is {1:.2f} seconds".format(url, t1 - t0))
    logging.debug("\n")
    return  # convert_one(url)


def convert_one(url):
    """
    Convert a single URL.
    """

    if url.lower().startswith("http"):
        response = requests.get(url)
        content = response.content
    else:
        with open(url, "rb") as f:
            content = f.read()

    scraperwiki.sql.execute("DROP TABLE IF EXISTS feature")
    scraperwiki.sql.execute("DROP TABLE IF EXISTS polygon")

    features = []
    polygons = []
    # Try to parse JSON and if that fails, assume KML
    try:
        # Avoid using response.json() because it assumes ISO-8859-1 instead of
        # utf-8 when the server doesn't say. And as per
        # https://tools.ietf.org/html/rfc7159 JSON will most likely be
        # encoded in utf-8. Passing the raw (byte) string to json.loads()
        # does the Right Thing.
        j = json.loads(content)
        features, polygons = parse_geojson(j, features, polygons)
    except:
        # Handle KML using the fastkml library
        k = kml.KML()
        k.from_string(content)
        features, polygons = parse_kml(k, features, polygons)

    logging.debug(("Writing {} features, and {} polygon elements to db".format(
        len(features), len(polygons))))
    scraperwiki.sql.save([], features, table_name="feature")
    scraperwiki.sql.save([], polygons, table_name="polygon")


def parse_geojson(j, features, polygons):
    """
    Take a geojson dictionary and parse out points, polygons and multipolygons
    into features and polygons arrays
    """

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
            add_polygon(row, feature_index, polygons, geometry['coordinates'])
        if geometry.get('type') == "MultiPolygon":
            add_multi_polygon(row, feature_index, polygons, geometry)

        features.append(row)

    return features, polygons


def parse_kml(k, features, polygons):
    """
    Take a fastkml object and parse out points, polygons and multipolygons
    into features and polygons arrays
    """
    # KML files can have features, folders or document at the root level
    # Documents and Folders can be nested inside one another
    #
    folders = []
    folder_names = []

    # Folders can exist inside folders and Documents hence we recurse
    folders, folder_names = walk_kml_tree(k, folders, folder_names)

    # We need to have a list of folders at this point with a matching list of
    # folder names. Each folder contains a list of features

    for i, folder in enumerate(folders, start=0):
        folder_name = folder_names[i]
        for feature_index, feature in enumerate(folder, start=1):
            # We store the str, int and float attributes of a feature
            attributes = [a for a in dir(feature) if a[0] is not "_"]
            row = {}
            for a in attributes:
                try:
                    value = getattr(feature, a)
                    if type(value) in [str, int, float]:
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
    """
    Take fastkml geometry object and put coordinates of points into features array.
    Coordinates of Polygons and MultiPolygons into polygons array
    """
    if not geometry:
        return features, polygons
    if geometry.geom_type == "Point":
        add_point(row, geometry.coords[0])
        features.append(row)
    if geometry.geom_type == "Polygon":
        add_polygon(row, feature_index, polygons, [geometry.exterior.coords],
                    folder_name=folder_name)
        # features.append(row)
    if geometry.geom_type == "MultiPolygon":
        # Multipolygons are handled by add_polygon, not add_multi_polygon
        # which is used for geojson, this may be a Bad Thing
        kml_polygons = [p.exterior.coords for p in geometry.geoms]
        add_polygon(row, feature_index, polygons, kml_polygons,
                    folder_name=folder_name)
    if geometry.geom_type == "GeometryCollection":
        for g in list(geometry.geoms):
            row, features, polygons = add_kml_geometry(
                features, row, polygons, feature_index, folder_name, g)

    return row, features, polygons


def walk_kml_tree(k, folders, folder_names):
    """
    Walk the KML tree recursively, Documents and Folders can lie within one
    another. Placemarks are the leaf nodes
    """
    if type(k) is kml.Placemark:
        # Feature at top level
        folders.append([k])
        if len(folder_names) == 0:
            folder_names = ["Feature"]
        else:
            folder_names.append(k.name)
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
            folder_names = [kml_features[0].name]  # kml_features[0].name
        else:
            # kml_features[0].name)
            folder_names.append(kml_features[0].name)
    elif type(kml_features[0]) is kml.Placemark:
        # Feature at top level
        feature_list = kml_features
        folders.append(feature_list)
        if len(folder_names) == 0:
            folder_names = ["Feature"]
        else:
            folder_names.append("Feature")

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


def add_polygon(row, feature_index, polygons, coordinates, folder_name=None):
    """
    Extract the data for a polygon from the geometry dict, and
    add several rows to the `polygons` list.
    """
    global global_polygon_index
    for polygon_index, points in enumerate(coordinates, start=1):
        global_polygon_index = global_polygon_index + 1
        for point_index, point in enumerate(points, start=1):
            row['folder_name'] = folder_name
            row['feature_index'] = feature_index
            row['polygon_index'] = global_polygon_index
            row['point_index'] = point_index
            row['longitude'] = point[0]
            row['latitude'] = point[1]

            polygons.append(row)
    return


def add_multi_polygon(row, feature_index, polygons, geometry, folder_name=None):
    """
    Extract the data for multiple polygons from the geometry dict, and
    add several rows to the `polygons` list.
    """
    global global_polygon_index
    assert geometry.get('type') == "MultiPolygon"

    coordinates = geometry['coordinates']
    for polygon_index, points in enumerate(coordinates, start=1):
        global_polygon_index = global_polygon_index + 1
        for point_index, point in enumerate(points[0], start=1):
            row['folder_name'] = folder_name
            row['feature_index'] = feature_index
            row['polygon_index'] = global_polygon_index
            row['point_index'] = point_index
            row['longitude'] = point[0]
            row['latitude'] = point[1]

            polygons.append(row)
    return


if __name__ == '__main__':
    main()
