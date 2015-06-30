#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 13:21:54 2015

@author: Olivier Bézie

The input is a XML OSM data set for the Dinan/Saint-Malo area in France
The output is a list of dictionaries
that look like this:

{
"id": "2406124091",
"basic_elem: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

The follwing filters has been applied:
- you should process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array,
      for use in geospacial indexing. Make sure the values inside "pos" array are floats
      and not strings. 
- if second level tag "k" value contains problematic characters, it should be ignored
- if second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if second level tag "k" value does not start with "addr:", but contains ":", you can process it
  same as any other tag.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- the address values are also under a key "address". They are processed in
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}

- City names with different spelling are all aligned to the most common one.
for example "Saint Malo" is changed into "Saint-Malo"

- the key "NOM" is replaced with the standard key "name"

- the key CEMT and its value are processed in :
"waterway": {
    "value": <source value if exists>
    "classtype": "CEMT",
    "class": "0" (the CEMT key value) 
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_refs": ["305896090", "1719825889"]


"""

import xml.etree.cElementTree as ET
import re
import codecs
import json

filename = "from_Dinan_to_StMalo"

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
multi_colon = re.compile(r'^([a-z]|_|[A-Z])*:([a-z]|_|[A-Z])*:')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

rightCityName = {"Saint Malo": "Saint-Malo"}

keyByTag = {"node":set(),"way":set()}

def parseAddress(value):
    [housenumber, street] = value.split(', ')
    return housenumber, street

def correctCitySpelling(city):
    if city in rightCityName.keys():
        return rightCityName[city]
    else:
        return city

def correctHouseNumber(value):
    i = 0
    for char in value:
        if re.search(r"[0-9]", char):
            i += 1
            continue
        else: 
            break
    
    if re.search(r"[a-z]|[A-Z]", char):
        value = value[:i] + " " + value[i:]
        
    return value

def intoDict(node, key, subkey, value):
    try:
        node[key][subkey] = value
    except:
        node[key] = {}
        node[key][subkey] = value
        
    return node

def intoArray(node, array, elem, value):
    try:
        node[array][elem] = value
    except:
        node[array] = [0.0, 0.0]
        node[array][elem] = value
    
    return node

def shape_element(element):
    node = {}
    
    if element.tag == "node" or element.tag == "way":
        node["basic_elem"] = element.tag
        for key in element.attrib.keys():
            keyByTag[element.tag].add(key)
            value = element.attrib[key]
            
            if key in CREATED:
                node = intoDict(node, "created", key, value)
            elif key == "lat":
                node = intoArray(node, "pos", 0, float(value))
            elif key == "lon":
                node = intoArray(node, "pos", 1, float(value))
            else:
                node[key] = value
        
        for tagElem in element.iterfind("tag"):
            key = tagElem.attrib['k']
            value = tagElem.attrib['v']
            
            if re.search(problemchars, key) or re.search(multi_colon, key):
                continue
            
            #replace the local key "NOM" with a standard key "name"
            elif key == "NOM": 
                node["name"] = value
            
            #include this river info under the standard key "waterway"
            elif key == "waterway":
                node = intoDict(node, key, "value", value)

            elif key == "CEMT":
                node = intoDict(node, "waterway", "classtytpe", key)
                node = intoDict(node, "waterway", "class", value)    
                
            elif key == "address":
                housenumber, street = parseAddress(value)
                node = intoDict(node, key, "housenumber", housenumber)
                node = intoDict(node, key, "street", street)
                
            elif re.search(r"^addr:", key) and re.search(lower_colon, key):
                keyByTag[element.tag].add(key)
                key = key.split(":")[1]
                
                if key == "city":
                    value = correctCitySpelling(value)
                elif key == "housenumber":
                    value = correctHouseNumber(value)
                
                node = intoDict(node, "address", key, value)
                    
            else:
                keyByTag[element.tag].add(key)
                node[key] = value
         
        for tagElem in element.iterfind("nd"):
            try: 
                node["node_refs"].append(tagElem.attrib['ref'])
            except:
                node["node_refs"] = [tagElem.attrib['ref']]
        
        return node

    else:
        return None


def process_map(filename, pretty):
    file_in = "raw\\{0}.osm".format(filename)
    file_out = "data\\{0}.json".format(filename)
    data = []
    with codecs.open(file_out, "w","UTF-8") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data


if __name__ == "__main__":
    process_map(filename, False)
    for tag in keyByTag.keys():
        print "Attributes in tag {0}: {1}".format(tag,sorted(keyByTag[tag]))
        for attrib in keyByTag[tag]:
            if re.search(r"[A-Z]", attrib):
                print attrib