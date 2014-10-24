# Advanced Project Management
# Parser & Metadata Downloader (PMD)
# Christian Grevisse (0100335342)
# University of Luxembourg - FSTC - MICS 3

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests, json, urllib, urllib.request, html, xml.etree.ElementTree as ET
from multiprocessing import Pool

def decode(s):
    return s.encode('utf-8','ignore').decode('ascii','ignore').strip()

class Block:
    def __init__(self, pmid, sentence, score, components):
        self.pmid = pmid
        self.sentence = sentence
        self.score = score
        self.components = components
        self.getMetadata()
        
    def getMetadata(self):
        url = "http://www.ncbi.nlm.nih.gov/pubmed/?term={}&report=xml&format=text".format(self.pmid)
        f = urllib.request.urlopen(url)
        root = ET.fromstring(html.unescape(f.read().decode('utf-8')))
        
        self.title = decode(next(root.iter('ArticleTitle')).text)
        self.journal = decode(next(root.iter('Title')).text)
        
        try:
            self.abstract = decode(next(root.iter('AbstractText')).text)
        except:
            self.abstract = ""
        
        try:
            try:
                self.year = decode(next(root.iter('PubDate')).find('Year').text)
            except:
                self.year = decode(next(root.iter('ArticleDate')).find('Year').text)
        except:
            self.year = 0    
        
        # DOI
        #jsonURL = "http://www.pmid2doi.org/rest/json/doi/{}".format(self.pmid)
        #response = urllib.request.urlopen(jsonURL)
        #jsonObj = json.loads(response.read().decode("utf-8"))
        
        self.doi = ""
        for articleID in root.iter('ArticleId'):
            if articleID.attrib["IdType"] == "doi":
                self.doi = decode(articleID.text).strip()
        
        self.authors = []
        for author in root.iter('Author'):
            try:
                firstname = decode(author.find('ForeName').text)
                surname = decode(author.find('LastName').text)
                self.authors.append("{}, {}".format(surname, firstname))
            except:
                pass
         
    def __str__(self):
        return "PubMed ID {}: {} ({})\n{}\n\t{} ({}) in {}, {} [DOI: {}]\n\tAbstract: {}\n".format(self.pmid, self.sentence, self.score, "\n".join(str(component) for component in self.components), self.title, "; ".join(self.authors), self.journal, self.year, self.doi, self.abstract)
        
class Component:
    def __init__(self, kind, name, start, end):
        self.kind = kind
        self.start = start
        self.end = end
        self.name = name
        
    def __str__(self):
        return "\t{} '{}' (Position: {}-{})".format(self.kind, self.name, self.start, self.end)

class Parser:

    def __init__(self):
        self.blocks = []
        
    def read(self, inputFile, numberOfWorkerThreads = 10):
        with open(inputFile, 'r', encoding = 'utf8') as input:
            lines = [line.encode('ascii', 'ignore').decode('ascii').strip() for line in input.readlines()]
            
            currentBlockLines = []
            allBlockLines = []
            
            for line in lines:
                if line != "":
                    currentBlockLines.append(line)
                else:
                    # new block incoming
                    allBlockLines.append(currentBlockLines)
                    currentBlockLines = []
                    
            # pool the jobs to create blocks and retrieve related article metadata
            pool = Pool(numberOfWorkerThreads)
            pool.map(self.createBlock, allBlockLines)
        
    def createBlock(self, blockLines):
        headLineComponents = blockLines[0].split("\t")
        
        pmid = headLineComponents[1]
        sentence = headLineComponents[2]
        score = float(headLineComponents[3])
        components = []
        
        for line in blockLines[1:]:
            lineComponents = line.split("\t")
            
            kind = lineComponents[0] # Proteins: PROTEIN / Interaction Keywords: PATTERN
            startEnd = lineComponents[1].split(" ")
            start = startEnd[0]
            end = startEnd[1]
            name = lineComponents[2] # Proteins: protein_name / Interaction Keywords: interaction_type
            
            components.append(Component(kind, name, start, end))
        
        b = Block(pmid, sentence, score, components)
        print(b)
                
def main():
    p = Parser()
    for inputFile in ["1.txt", "2.txt"]:
        p.read(inputFile)
    
if __name__ == "__main__":
    main()