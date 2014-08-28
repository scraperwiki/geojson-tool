#!/usr/bin/env python

from __future__ import print_function
import json
import os
import sys

import requests

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
    j = response.json()
    scraperwiki.sql.execute("DROP TABLE IF EXISTS swdata")
    features = []
    for feature in j['features']:
        # The row we are going to add;
        # it's the properties of the feature.
        row = feature['properties']
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
            coordinates = geometry['coordinates']
            longitude, latitude = coordinates[:2]
            if len(coordinates) > 2:
                row['elevation'] = coordinates[2]
            row['longitude'] = longitude
            row['latitude'] = latitude
        features.append(row)
    scraperwiki.sql.save([], features)

if __name__ == '__main__':
    main()
