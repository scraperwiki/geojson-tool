geojson-tool
============

GeoJSON Tool on ScraperWiki

## Credits

The icon uses Simple_Globe.svg from
http://commons.wikimedia.org/wiki/File:Simple_Globe.svg

## KML test script for ipython
"""
import requests
from fastkml import kml
url = "https://dl.dropboxusercontent.com/u/21886071/countries_world.kml"
response = requests.get(url)
k = kml.KML()
k.from_string(response.content)
"""

