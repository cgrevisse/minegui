from app import db
import urllib, html, xml.etree.ElementTree as ET

ontologyDBs = {
	'urn:miriam:cas' : 'Chemical Abstracts Service', 
	'urn:miriam:obo.chebi' : 'Chebi', 
	'urn:miriam:chembl.compound' : 'ChEMBL', 
	'urn:miriam:chembl.target' : 'ChEMBL target', 
	'urn:miriam:drugbank' : 'DrugBank', 
	'urn:miriam:drugbankv4.target' : 'DrugBank Target v4', 
	'urn:miriam:ec-code' : 'Enzyme Nomenclature', 
	'urn:miriam:ensembl' : 'Ensembl', 
	'urn:miriam:ncbigene' : 'Entrez Gene', 
	'urn:miriam:obo.go' : 'Gene Ontology', 
	'urn:miriam:hgnc' : 'HGNC', 
	'urn:miriam:hgnc.symbol' : 'HGNC Smbol', 
	'urn:miriam:hmdb' : 'HMDB', 
	'urn:miriam:interpro' : 'InterPro', 
	'urn:miriam:kegg.compound' : 'Kegg Compound', 
	'urn:miriam:kegg.genes' : 'Kegg Genes', 
	'urn:miriam:kegg.pathway' : 'Kegg Pathway', 
	'urn:miriam:kegg.reaction' : 'Kegg Reaction', 
	'urn:miriam:mesh.2012' : 'MeSH 2012', 
	'urn:miriam:mgd' : 'Mouse Genome Database', 
	'urn:miriam:panther.family' : 'PANTHER Family', 
	'urn:miriam:pharmgkb.pathways' : 'PharmGKB Pathways', 
	'urn:miriam:pubchem.compound' : 'PubChem-compound', 
	'urn:miriam:pubchem.substance' : 'PubChem-substance', 
	'urn:miriam:pubmed' : 'PubMed', 
	'urn:miriam:reactome' : 'Reactome', 
	'urn:miriam:refseq' : 'RefSeq', 
	'urn:miriam:taxonomy' : 'Taxonomy', 
	'urn:miriam:uniprot' : 'Uniprot', 
	'urn:miriam:wikipathways' : 'WikiPathways', 
	'urn:miriam:wikipedia.en' : 'Wikipedia (English)'
}

class EnsemblHGNCMap(db.Model):
    __tablename__ = "ensemblHGNCMap"

    ensemblProteinID = db.Column(db.String(100), primary_key = True)
    hgncSymbol = db.Column(db.String(100), primary_key = True)

class OntologyAnnotation(db.Model):
    __tablename__ = "ontologyAnnotation"
    
    id = db.Column(db.Integer, primary_key = True)
    urn = db.Column(db.String(100))
    identifier = db.Column(db.String(100))
    default = db.Column(db.Boolean)
    
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'))
    
    def __repr__(self):
        return str(self.serialize)
    
    def allURIs(self):
        url = "http://www.ebi.ac.uk/miriamws/main/rest/resolve/{}:{}".format(self.urn, self.identifier)
        
        uris = []
        
        try:
            f = urllib.request.urlopen(url)
            root = ET.fromstring(html.unescape(f.read().decode('utf-8')))
            
            for uri in root.iter('uri'):
                if(not ("deprecated" in uri.attrib and uri.attrib["deprecated"] == "true") and ("type" in uri.attrib and uri.attrib["type"] == "URL")):
                    uris.append(uri.text)
        except urllib.error.HTTPError:
            pass

        return uris
    
    @property
    def uri(self):
        uris = self.allURIs()
        
        if len(uris) > 0:
            return uris[0]
        else:
            return ""
    
    @property
    def serialize(self):
        return {
            'id': self.id,
            'dbName': ontologyDBs[self.urn],
            'urn': self.urn,
            'identifier': self.identifier,
            'default': self.default,
            'entity_id': self.entity_id
        }

class Keyword(db.Model):
    __abstract__ = True
    __tablename__ = "keyword"
    
    id = db.Column(db.Integer, primary_key = True)
    start = db.Column(db.Integer)
    end = db.Column(db.Integer)
    grade = db.Column(db.Integer)
    comment = db.Column(db.String(200))
    
class Entity(Keyword):
    __tablename__ = "entity"
    
    type = db.Column(db.Enum("Protein", "Disease", "Go-Process", "Chemical"))
    software = db.Column(db.Enum("Genia", "Reflect", "Exact", ""))
    name = db.Column(db.String(100))
    databaseID = db.Column(db.String(50))
    
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentence.id'))
    
    ontologyAnnotations = db.relationship('OntologyAnnotation', backref = 'entity', lazy = "joined") # join_depth=2 
    
    def __repr__(self):
        return str(self.serialize)
    
    @property
    def ontologyLink(self):
        
        if len(self.ontologyAnnotations) == 0:
            return ""
        
        annotation = None
        
        for oa in self.ontologyAnnotations:
            if oa.default:
                annotation = oa
                break
            
        if annotation == None:
            annotation = self.ontologyAnnotations[0]
            
        return annotation.uri

    @property
    def serialize(self):
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'software': self.software,
            'databaseID': self.databaseID,
            'start': self.start,
            'end': self.end,
            'grade': self.grade,
            'comment': self.comment,
            'ontologyAnnotations': [oa.serialize for oa in self.ontologyAnnotations],
            'ontologyLink': self.ontologyLink, 
            'sentence_id': self.sentence_id
        }
    
    def createLinkDict(self, type, id, url, defaultAnnotation = False):
        return { 'type': type, 'id': id, 'url': url, 'defaultAnnotation': defaultAnnotation }
    
    def links(self):
        
        databaseIDLinks = []
        
        # links based on databaseID
        if self.type == "Protein":
            # map ensembl to hgnc
            mappings =  EnsemblHGNCMap.query.filter(EnsemblHGNCMap.ensemblProteinID == self.databaseID).all()
            
            for mapping in mappings:
                databaseIDLinks.append(self.createLinkDict("HGNC", mapping.hgncSymbol, "http://www.genenames.org/cgi-bin/search?search_type=symbols&search={}".format(mapping.hgncSymbol)))
        elif self.type == "Disease":
            id = self.databaseID.replace('DOID:', '')
            databaseIDLinks.append(self.createLinkDict("Disease", id, "http://disease-ontology.org/term/DOID%3A{}".format(id)))
        elif self.type == "Go-Process":
            databaseIDLinks.append(self.createLinkDict("Go-Process", self.databaseID, "http://www.ebi.ac.uk/QuickGO/GTerm?id={}".format(self.databaseID)))
        elif self.type == "Chemical":
            id = self.databaseID.replace("CID", "")
            databaseIDLinks.append(self.createLinkDict("Chemical", id, "https://pubchem.ncbi.nlm.nih.gov/compound/{}".format(id)))
        else:
            pass

        ownOntologyAnnotationLinks = []

        # own annotations
        for oa in self.ontologyAnnotations:
            for uri in oa.allURIs():
                ownOntologyAnnotationLinks.append(self.createLinkDict(ontologyDBs[oa.urn], oa.identifier, uri, defaultAnnotation = oa.default))
            
        return { 'dbLinks': databaseIDLinks, 'ownLinks': ownOntologyAnnotationLinks }
    
class Interaction(Keyword):
    __tablename__ = "interaction"
    
    type = db.Column(db.String(100))
    
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentence.id'))
    
    def __repr__(self):
        return str(self.serialize)
    
    @property
    def serialize(self):
        return {
            'id': self.id,
            'type': self.type,
            'start': self.start,
            'end': self.end,
            'grade': self.grade,
            'comment': self.comment,
            'sentence_id': self.sentence_id
        }
    
class Sentence(db.Model):
    __tablename__ = "sentence"

    id = db.Column(db.Integer, primary_key = True)
    pubmedID = db.Column(db.Integer)
    sentenceID = db.Column(db.Integer)
    literal = db.Column(db.String(500))
    score = db.Column(db.Float)
    grade = db.Column(db.Integer)
    comment = db.Column(db.Text)
    
    # lazy = 'dynamic'
    entities = db.relationship('Entity', backref = 'sentence', lazy="joined", join_depth=2)
    interactions = db.relationship('Interaction', backref = 'sentence', lazy="joined", join_depth=2) 
    
    def __repr__(self):
        return str(self.serialize)
    
    @property
    def serialize(self):
        return {
            'id': self.id,
            'pubmedID': self.pubmedID,
            'sentenceID': self.sentenceID,
            'literal': self.literal,
            'score': self.score,
            'grade': self.grade,
            'comment': self.comment,
            'entities': [e.serialize for e in self.entities],
            'interactions': [i.serialize for i in self.interactions]
        }
