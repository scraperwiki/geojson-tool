#!/usr/bin/env python

from __future__ import print_function
import sys

import requests

import scraperwiki

URL="http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"

def main(argv=None):
    if argv is None:
        argv = sys.argv
    arg = argv[1:]

    # Expects one argument.
    url = arg[0]
    return convert_one(url)

def convert_one(url):
    response = requests.get(url)
    j = response.json()
    scraperwiki.sql.execute("DROP TABLE IF EXISTS swdata")
    for feature in j['features']:
        d = feature['properties']
        if 'id' in feature:
            d['id'] = feature['id']
        g = feature.get('geometry')
        if g and g.get('type') == "Point":
            coordinates = g['coordinates']
            longitude, latitude = coordinates[:2]
            if len(coordinates) > 2:
                d['elevation'] = coordinates[2]
            d['longitude'] = longitude
            d['latitude'] = latitude
        scraperwiki.sql.save([], d)

if __name__ == '__main__':
    main()
