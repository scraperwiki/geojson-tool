#!/usr/bin/env python

"""
shpit.py thing.shp
"""

import json
import sys

from collections import OrderedDict

# https://github.com/scraperwiki/scraperwiki-python
import scraperwiki
# A shapefile module. See
# http://www.esri.com/library/whitepapers/pdfs/shapefile.pdf
# for the shapefile pay.
# https://pypi.python.org/pypi/pyshp/1.1.4
import shapefile

def shape1(fname):
    sf = shapefile.Reader(fname)
    meta = {}

    shapes = sf.shapes()
    meta['n_shapes'] = len(sf.shapes())
    meta['n_records'] = len(sf.records())
    meta['fields'] = sf.fields[1:]

    json.dump(meta, sys.stdout, indent=2)
    print ""

    print "types", set(shape.shapeType for shape in sf.shapes())
    sys.stderr.write("\n")
    for feature_index, sr in enumerate(sf.shapeRecords(), start=1):
        if sr.shape.shapeType == 5:
            polygon(sf, feature_index, sr)
            sys.stderr.write("\rShape {}".format(feature_index))
        else:
            sys.stderr.write(
              "Shape {} (1-based) has shape Type {}\n".format(
                feature_index, sr.shape.shapeType))

        # Each Shape becomes a row in the feature table; each field
        # becomes a column.
        feature_dict = OrderedDict([
            ('feature_index', feature_index),
          ])
        fieldnames = [f[0] for f in sf.fields[1:]]
        feature_dict.update(zip(fieldnames, sr.record))
        scraperwiki.sql.save(
          ['feature_index'],
          feature_dict,
          table_name='feature'
        )

def polygon(shapefile, feature_index, sr):
    """`sr` is a shapeRecord."""

    points = sr.shape.points
    parts = sr.shape.parts
    parts = list(parts) + [len(points)]
    for polygon_index, (start, end) in enumerate(
      zip(parts, parts[1:]), start=1):
        for point_index, point in enumerate(points[start:end], start=1):
            row = OrderedDict([
              ('feature_index', feature_index),
              ('polygon_index', polygon_index),
              ('point_index', point_index),
              ('longitude', point[0]),
              ('latitude', point[1]),
              ])
            scraperwiki.sql.save(
              ['feature_index', 'polygon_index', 'point_index'],
              row,
              table_name='polygon')

def usage(out=sys.stdout):
    out.write(__doc__.strip() + '\n')
    return 2

def main(argv=None):
    if argv is None:
        argv = sys.argv

    arg = argv[1:]
    if not arg:
        sys.stderr.write("An argument is required.\n")
        return usage(sys.stderr)

    shape1(arg[0])

if __name__ == '__main__':
    main()
