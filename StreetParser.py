#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 17:34:12 2015

@author: Olivier Bézie

input: html web page containing the list of streets for a given city:
http://www.annuaire-mairie.fr/rue-cancale.html
http://www.annuaire-mairie.fr/rue-dinan.html
http://www.annuaire-mairie.fr/rue-dinard.html
http://www.annuaire-mairie.fr/rue-saint-lunaire.html
http://www.annuaire-mairie.fr/rue-saint-malo.html

output: json file named list_of_Streets.json:
{<city_name1>:{<street_type1>:[list of street fo streetype1],
               <street_type2>:[list of street fo streetype2],
               ...}
 <city_name2>:{<street_type1>:[list of street fo streetype1],
               <street_type2>:[list of street fo streetype2],
               ...}
...
}

- the input file content could not be processed because of a character prefixed with "&". So all "&" has been removed. Such character does not appear in the address information.

"""
import xml.etree.cElementTree as ET
import pprint
import codecs
import unicodedata
import json

cities = ["Cancale", "Dinan", "Dinard", "Saint-Lunaire", "Saint-Malo"]

pathToStreetType = "./body/div{page}/div{content}/div{h2div}"

problemchar = "&"

streetNames = set()
nbStreets = {}

def cleanFile(filename):
    cleanedLine = ""
    
    file_in = "{0}.html".format(filename)
    with codecs.open(file_in, "r","UTF-8") as rawf:
        rawLines = rawf.readlines()
    
    cleanedFile = "{0}_cleaned.html".format(filename)
    with codecs.open(cleanedFile, "w","UTF-8") as cleanedf:
        for rawLine in rawLines:
            cleanedLine += rawLine.strip()
        
        cleanedLine = cleanedLine.replace("itemscope ", "")
        cleanedLine = cleanedLine.replace("async ", "")
        cleanedLine = cleanedLine.replace(problemchar, "")
        cleanedf.write(cleanedLine)
        
    return cleanedFile

def streetClassString(streetType):
    streetClass = streetType.replace(" ", "-").lower()+"_content"
    
    # an attribute only contains ASCII characters
    # French accentuated characters are replaced with non-accentuated character
    streetClass = unicodedata.normalize('NFKD', unicode(streetClass))
    streetClass = codecs.encode(streetClass, 'ASCII', 'ignore')
    
    return streetClass

def extract_streets(): 
    cityStreets = {}
    for city in cities:
        print city
        cityStreets[city] = {}
        nbStreets[city] = 0
        
        filename = "raw\\rue-"+city
        cleanedFile = cleanFile(filename)
            
        tree = ET.parse(cleanedFile)
        root = tree.getroot()
        streetTypes = root.find('.//h3/..[@class="h2div"]')
    
        for type in streetTypes.findall("h3"):
            streetType = type.text.split(" ")[0]
            streetClass = streetClassString(streetType)
            streets = []
            
            streetNode = ".//*[@class='"+streetClass+"']/table/tr/td"
            for street in root.findall(streetNode):
                if street.text != "nbsp;":
                    streets.append(street.text)
                    nbStreets[city] += 1
    
            cityStreets[city][streetType] = streets
    
            streetNames.add(streetType)

        print "number of street in {0}: {1}".format(city, nbStreets[city])
    for streetName in streetNames:
        print streetName
    
    return cityStreets    
   
if __name__ == "__main__":
    cityStreets = extract_streets()
   
    with codecs.open("data\\list_of_Streets.json", "w") as jsonf:
        json.dump(cityStreets, jsonf)