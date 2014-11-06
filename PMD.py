# Advanced Project Management
# Parser & Metadata Downloader (PMD)
# Christian Grevisse (0100335342)
# University of Luxembourg - FSTC - MICS 3

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, requests, json, urllib, urllib.request, html, xml.etree.ElementTree as ET
from multiprocessing import Pool

downloadMetaData = True

def decode(s):
    return s.encode('utf-8','ignore').decode('ascii','ignore').strip()

class Block:
    def __init__(self, pmid, sentenceID, sentence, score, components):
        self.pmid = pmid
        self.sentenceID = sentenceID
        self.sentence = sentence
        self.score = score
        self.components = components
        
        if downloadMetaData: 
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
        if downloadMetaData:
            return "PubMed ID {} (Sentence: {}): {} ({})\n{}\n\t{} ({}) in {}, {} [DOI: {}]\n\tAbstract: {}\n".format(self.pmid, self.sentenceID, self.sentence, self.score, "\n".join(str(component) for component in self.components), self.title, "; ".join(self.authors), self.journal, self.year, self.doi, self.abstract)
        else:
            return "PubMed ID {} (Sentence: {}): {} ({})\n{}\n".format(self.pmid, self.sentenceID, self.sentence, self.score, "\n".join(str(component) for component in self.components))
        
class Interaction:
    def __init__(self, type, start, end):
        self.type = type
        self.start = start
        self.end = end
        
    def __str__(self):
        return "\tPattern '{}' (Position: {}-{})".format(self.type, self.start, self.end)

class Entity:
    def __init__(self, type, software, name, databaseID, start, end):
        self.type = type
        self.software = software
        self.name = name
        self.databaseID = databaseID
        self.start = start
        self.end = end
        
    def __str__(self):
        return "\t{} '{}' (Software: {}, Position: {}-{}, Database ID: {})".format(self.type, self.name, self.software, self.start, self.end, self.databaseID)

class Parser:

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
        
        ids = headLineComponents[1].split("__")
        pmid = ids[0]
        sentenceID = ids[1]
        sentence = headLineComponents[2]
        score = float(headLineComponents[3])
        components = []
        
        for line in blockLines[1:]:
            lineComponents = line.split("\t")
            
            # Possible forms:
            # PROTEIN_EXACT\tstart end\tword\tdatabase id
            # PROTEIN_GENIA\tstart end\tword\tPROTEIN_REFLECT\tstart end\tword\tdatabase id
            # PATTERN\tstart end\tinteraction_type
            
            try:
                kind = lineComponents[0]
            
                if kind == "PATTERN":
                    start, end = self.startEnd(lineComponents[1])
                    type = lineComponents[2]
                    components.append(Interaction(type, start, end))
                else:
                    type, software = self.typeSoftware(kind)
                
                    if software.upper() == "EXACT":
                        start, end = self.startEnd(lineComponents[1])
                        name = lineComponents[2]
                        databaseID = lineComponents[3]
                        components.append(Entity(type, software, name, databaseID, start, end))
                    else:
                        # partial overlap
                        databaseID = lineComponents[6]
                    
                        type1, software1 = self.typeSoftware(lineComponents[0])
                        start1, end1 = self.startEnd(lineComponents[1])
                        name1 = lineComponents[2]
                    
                        components.append(Entity(type1, software1, name1, databaseID, start1, end1))
                    
                        type2, software2 = self.typeSoftware(lineComponents[3])
                        start2, end2 = self.startEnd(lineComponents[4])
                        name2 = lineComponents[5]
                    
                        components.append(Entity(type2, software2, name2, databaseID, start2, end2))
            except:
                print("Error: {}\n\nLine Components: {}".format(sys.exc_info()[0], lineComponents))
                raise
        
        b = Block(pmid, sentenceID, sentence, score, components)
        print(b)
        
    def startEnd(self, s):
        se = s.split(" ")
        return se[0], se[1]
        
    def typeSoftware(self, s):
        ts = s.split("_")
        return ts[0].lower().title(), ts[1].lower().title()
                
def main():
    
    if len(sys.argv) != 2:
        print("Usage: python3 PMD.py <inputFile>")
        return
    
    inputFile = sys.argv[1]
    p = Parser()
    p.read(inputFile)
    
if __name__ == "__main__":
    main()