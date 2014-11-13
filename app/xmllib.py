# -*- coding: utf-8 -*-

from xml.etree import ElementTree

def xml2dict(element):
    if not isinstance(element, ElementTree.Element):
        raise ValueError("must pass xml.etree.ElementTree.Element object")

    def xmltodict_handler(parent_element):
        result = dict()
        for element in parent_element:
            if len(element):
                obj = xmltodict_handler(element)
            else:
                obj = element.text

            if result.get(element.tag):
                if hasattr(result[element.tag], "append"):
                    result[element.tag].append(obj)
                else:
                    result[element.tag] = [result[element.tag], obj]
            else:
                result[element.tag] = obj
        return result

    return {element.tag: xmltodict_handler(element)}


def dict2xml(element):
    #if not isinstance(element, dict):
    #    raise ValueError("must pass dict type")
    #if len(element) != 1:
    #    raise ValueError("dict must have exactly one root key")

    def dicttoxml_handler(result, key, value):
        if isinstance(value, list):
            res = ElementTree.Element(key)
            for e in value:
                dicttoxml_handler(res, naive_stemming(key), e)
            result.append(res)
                
        elif isinstance(value, str):
            elem = ElementTree.Element(key)
            elem.text = value
            result.append(elem)
        elif isinstance(value, int) or isinstance(value, float):
            elem = ElementTree.Element(key)
            elem.text = str(value)
            result.append(elem)
        elif value is None:
            result.append(ElementTree.Element(key))
        elif isinstance(value, dict):
            res = ElementTree.Element(key)
            for k, v in value.items():
                dicttoxml_handler(res, k, v)
            result.append(res)
        else:
            print("ERROR: Potential loss of data. TYPE:" + str(type(value)) )


    #print(type(element))
    if isinstance(element, list):
        result = ElementTree.Element( 'sentences' ) 
        for sentence in element:
            res = ElementTree.Element('sentence')        
            dicttoxml_handler(res, None, sentence)
            result.append(res)
        return result

    result = ElementTree.Element( 'sentence' )
    dicttoxml_handler(result, None, element)
    return result

def xmlfile2dict(filename):
    return xml2dict(ElementTree.parse(filename).getroot())

def dict2xmlfile(element, filename):
    ElementTree.ElementTree(dict2xml(element)).write(filename)

def xmlstring2dict(xmlstring):
    return xml2dict( ElementTree.fromstring(xmlstring) )

def dict2xmlstring(element):
    return str(ElementTree.tostring(dict2xml(element), 'UTF-8') , "utf-8")

def naive_stemming(s):
    if s.endswith("ies"):
        return s[:-3] + "y"
    elif s.endswith("s"):
        return s[:-1]


   
