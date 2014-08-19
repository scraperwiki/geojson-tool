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
    response = requests.get(url)
    j = response.json()
    scraperwiki.sql.execute("DROP TABLE IF EXISTS swdata")
    to_save = []
    for feature in j['features']:
        # `d` is the row we are going to add; it's the
        # properties of the point.
        d = feature['properties']
        # Add feature.id to the row if there is one.
        if 'id' in feature:
            # Avoid issue 3 which is when there is already a
            # property called "id" but with a different case.
            # https://github.com/scraperwiki/geojson-tool/issues/3
            # (we do not fix the general version of this case issue)
            keys = set(k.lower() for k in d.keys())
            if 'id' not in keys:
                d['id'] = feature['id']
        g = feature.get('geometry')
        if g and g.get('type') == "Point":
            coordinates = g['coordinates']
            longitude, latitude = coordinates[:2]
            if len(coordinates) > 2:
                d['elevation'] = coordinates[2]
            d['longitude'] = longitude
            d['latitude'] = latitude
        to_save.append(d)
    scraperwiki.sql.save([], to_save)

if __name__ == '__main__':
    main()
