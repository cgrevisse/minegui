from flask import render_template, request, jsonify, make_response, url_for, redirect
from app import app, db
from app.models import *
from json import dumps
from .xmllib import dict2xmlstring
import os, sys, csv, json, urllib, urllib.request, html, xml.etree.ElementTree as ET
import xml.dom.minidom

inputFilesDir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'inputFiles')
allowedFileExtensions = ['txt', 'xml']

defaultGrade = 0
defaultComment = ""


# Main page

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'POST':
		format = request.form['format']
		
		file = request.files['importFileInput']
		
		if file and len(file.filename) > 0 and file.filename.rsplit('.', 1)[1] in allowedFileExtensions:
			
			# create input files directory
			if not os.path.exists(inputFilesDir):
				os.makedirs(inputFilesDir)
			
			path = os.path.join(inputFilesDir, file.filename)
			file.save(path)
			importDataFromFile(path, format)
			
			# cleanup
			try:
				os.remove(path)
				os.removedirs(inputFilesDir)
			except OSError:
				pass
			
	return render_template('index.html')


# Rest Interface

@app.route('/sentences/')
def sentences():
	# return dumps([s.serialize for s in Sentence.query.all()])
	return dumps({"data":[s.serialize for s in Sentence.query.all()]})

@app.route('/sentences/<int:id>')
def sentence(id):
	return dumps(Sentence.query.get(id).serialize)

@app.route('/sentences/<int:id>/metadata')
def getMetadata(id):
	
	s = Sentence.query.get(id)
	
	url = "http://www.ncbi.nlm.nih.gov/pubmed/?term={}&report=xml&format=text".format(s.pubmedID)
	f = urllib.request.urlopen(url)
	root = ET.fromstring(html.unescape(f.read().decode('utf-8')))
	
	title = decode(next(root.iter('ArticleTitle')).text)
	journal = decode(next(root.iter('Title')).text)
	
	try:
	    abstract = decode(next(root.iter('AbstractText')).text)
	except:
	    abstract = ""
	
	try:
		try:
			year = decode(next(root.iter('PubDate')).find('Year').text)
		except:
			year = decode(next(root.iter('ArticleDate')).find('Year').text)
	except:
		year = 0    
	
	# DOI
	#jsonURL = "http://www.pmid2doi.org/rest/json/doi/{}".format(self.pmid)
	#response = urllib.request.urlopen(jsonURL)
	#jsonObj = json.loads(response.read().decode("utf-8"))
	
	doi = ""
	for articleID in root.iter('ArticleId'):
		if articleID.attrib["IdType"] == "doi":
			doi = decode(articleID.text).strip()
	
	authors = []
	for author in root.iter('Author'):
		try:
			firstname = decode(author.find('ForeName').text)
			surname = decode(author.find('LastName').text)
			authors.append("{}, {}".format(surname, firstname))
		except:
			pass
		
	return dumps({ 'title': title, 'authors': authors, 'journal': journal, 'year': year, 'abstract': abstract, 'doi': doi, 'pmid': s.pubmedID, 'sentenceID': s.sentenceID })

@app.route('/entity/<int:id>/links')
def entityLinks(id):
	entity = Entity.query.get(id)
	return dumps(entity.links())

@app.route('/feedback/', methods=['GET', 'POST'])
def saveFeedback():
	if request.method == 'POST':
		entityNum=int(request.form['entity_num'])
		for i in range(entityNum):
			entity = Entity.query.get(int(request.form['EntityID_'+str(i)]))
			entity.grade=int(request.form['EntityGrade_'+str(i)])
			entity.comment=request.form['EntityComment_'+str(i)]
		interactionNum=int(request.form['interaction_num'])
		for i in range(interactionNum):
			interaction= Interaction.query.get(int(request.form['InteractionID_'+str(i)]))
			interaction.grade=int(request.form['InteractionGrade_'+str(i)])
			interaction.comment=request.form['InteractionComment_'+str(i)]
		sentence=Sentence.query.get(int(request.form['SentenceID']))
		sentence.grade=request.form['SentenceGrade']
		sentence.comment=request.form['SentenceComment']
		db.session.commit()
		return dumps(sentence.serialize)
	else:
		return redirect(url_for('index'))


# Export

@app.route('/export/<int:id>')
def export_single(id):
	data = Sentence.query.get(id).__dict__
	# Delete ORM specific attribute
	del data['_sa_instance_state']
	data = eval(repr(data))
	xml = dict2xmlstring(data)
	return download(xml)

@app.route('/export/')
def export_all():
	data = []
	for s in Sentence.query.all():
		sdict = s.__dict__
		del sdict['_sa_instance_state']
		sdict = eval(repr(sdict))
		data.append(sdict)
	# Delete ORM specific attribute
	xml = dict2xmlstring(data)
	return download(xml)

def generate_export_filename():
	import datetime
	import time
	ts = time.time()
	return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S_export.xml')

def download(xmlString):
	""" build response to force download """
	filename = generate_export_filename()
	
	# pretty print
	xmlString = xml.dom.minidom.parseString(xmlString).toprettyxml()
	
	# We need to modify the response, so the first thing we 
	# need to do is create a response out of the XML string
	response = make_response(xmlString)
	# This is the key: Set the right header for the response
	# to be downloaded, instead of just printed on the browser
	response.headers["Content-Disposition"] = "attachment; filename=%s" % (filename)
	return response


# Ontologies

@app.route('/ontologyDBs')
def allOntologyDBs():
	return dumps(ontologyDBs)

@app.route('/addOntologyAnnotation', methods=['GET', 'POST'])
def addOntologyAnnotation():
	if request.method == 'POST':
		entityID = int(request.form['entityID'])
		databaseURN = request.form['databaseURN']
		identifier = request.form['identifier']
		
		# no identifier -> no ontology annotation
		if len(identifier) == 0:
			return dumps({})
		
		entity = Entity.query.get(entityID)
		
		default=False
		# if first ontology annotation for this entity, make it default
		if len(entity.ontologyAnnotations) == 0:
			default = True
		
		if 'default' in request.form:
			default = True
		# if new ontology annotation should be default, set default to false for all previous ones
		if default:
			for oa in entity.ontologyAnnotations:
				oa.default = False
		
		o = OntologyAnnotation(urn = databaseURN, identifier = identifier, default = default, entity = entity)
		
		db.session.add(o)
		db.session.commit()
		return dumps(o.serialize)

@app.route('/editOntologyAnnotation', methods=['GET', 'POST'])
def editOntologyAnnotation():
	if request.method == 'POST':
		entityID = int(request.form['entityID'])
		ontologyID = int(request.form['ontologyID'])
		databaseURN = request.form['databaseURN']
		identifier = request.form['identifier']
		entity = Entity.query.get(entityID)
		
		# no identifier -> no ontology annotation
		if len(identifier) == 0:
			return dumps({})
		
		o = OntologyAnnotation.query.get(ontologyID)
		o.urn=databaseURN
		o.identifier=identifier
		default=False
		# if only annotation make it default
		if len(entity.ontologyAnnotations) == 1:
			default = True
		
		if 'default' in request.form:
			default = True
		
		if o.default:
			default = True
		# if this ontology annotation should be default, set default to false for all previous ones
		if default:
			for oa in entity.ontologyAnnotations:
				oa.default = False
		
		o.default=default
		
		db.session.commit()
		return dumps(o.serialize)
		
@app.route('/removeOntologyAnnotation/<int:id>')
def deleteOntologyAnnotation(id):
	o = OntologyAnnotation.query.get(id)
	db.session.delete(o)
	db.session.commit()
	return dumps(o.serialize)

@app.route('/getOntologyAnnotation/<int:id>')
def getOntologyAnnotation(id):
	o = OntologyAnnotation.query.get(id)
	return dumps(o.serialize)


# Import

def corpusImport(inputFile):
	with open(inputFile, 'r', encoding = 'utf8') as input:
		coding = 'utf8' # 'ascii'
		lines = [line.encode(coding, 'ignore').decode(coding).strip() for line in input.readlines()]
		currentBlockLines = []
		allBlockLines = []

		currentBlockLines = []
		allBlockLines = []
		
		for line in lines:
			if line != "":
			    currentBlockLines.append(line)
			else:
			    # new block incoming
			    allBlockLines.append(currentBlockLines)
			    currentBlockLines = []

		for block in allBlockLines:
			createBlock(block)

def xmlImport(inputFile):
	def named_parameters(model):
		columns = [m.key for m in model.__table__.columns]
		return columns

	# Truncate DB
	Sentence.query.delete()
	Entity.query.delete()
	Interaction.query.delete()
	OntologyAnnotation.query.delete()
	db.session.commit()

	tree = ET.parse(inputFile)
	root = tree.getroot()
	for sentence in root:
		sentence_attr = { el.tag: el.text for el in sentence if el.text and el.tag in named_parameters(Sentence)}
		
		# Entity
		entities = []
		for entity in sentence.iter("entity"):
			entity_attr = { el.tag: el.text for el in entity if el.text and el.tag in named_parameters(Entity)}

			# Ontology Annotation
			ontologyAnnotations = []
			for ontologyAnnotation in entity.iter("ontologyAnnotation"):
				ontologyAnnotation_attr = { el.tag: el.text for el in ontologyAnnotation if el.text and el.tag in named_parameters(OntologyAnnotation)}
				ontologyAnnotation_attr["default"] = (ontologyAnnotation_attr["default"] == 'True')
				ontologyAnnotations.append( OntologyAnnotation(**ontologyAnnotation_attr) )

			if not "comment" in entity_attr: entity_attr["comment"] = ""

			entity_attr["ontologyAnnotations"] = ontologyAnnotations
			entities.append( Entity(**entity_attr)	)

		# Interaction
		interactions = []
		for interaction in sentence.iter("interaction"):
			interaction_attr = { el.tag: el.text for el in interaction if el.text and el.tag in named_parameters(Interaction)}
			if not "comment" in interaction_attr: interaction_attr["comment"] = ""
			interactions.append( Interaction(**interaction_attr) )

		sentence_attr["entities"] = entities
		sentence_attr["interactions"] = interactions
		if not "comment" in sentence_attr: sentence_attr["comment"] = ""

		s = Sentence(**sentence_attr)

		db.session.add(s)
	

	db.session.commit()

# 3 following methods: check whether not already within DB to avoid integrity errors !!!

def ensemblHGCNMapImport(inputFile):
	with open(inputFile, 'r') as input:
		lines = [line.strip() for line in input.readlines()[1:]] # header line included
		
		for line in lines:
			(ensemblProteinID, hgncSymbol) = line.split("\t")
			
			if len(EnsemblHGNCMap.query.filter_by(ensemblProteinID = ensemblProteinID, hgncSymbol = hgncSymbol).all()) == 0:
				db.session.add(EnsemblHGNCMap(ensemblProteinID = ensemblProteinID, hgncSymbol = hgncSymbol))
			
		db.session.commit()

def stringEntrezMapImport(inputFile):
	with open(inputFile, 'r') as input:
		stringEntrez = csv.reader(input, delimiter='\t')
		header = False
		for row in stringEntrez:
			if header is False: 
				header = True
			else:
				stringLocusID = row[1].strip()
				entrezGeneID = row[0].strip()
			
				if len(stringLocusID) and len(entrezGeneID) and len(StringEntrezMap.query.filter_by(stringLocusID = stringLocusID, entrezGeneID = entrezGeneID).all()) == 0:
					db.session.add(StringEntrezMap(stringLocusID = stringLocusID, entrezGeneID = entrezGeneID))
				
		db.session.commit()
		
		updateStringEntrezHGNCMap()

def entrezHGNCMapImport(inputFile):
	with open(inputFile) as input:
		entrezHGNC = csv.reader(input, delimiter='\t')
		header = False
		for row in entrezHGNC:
			if header is False: 
				header = True
			else:
				# Columns: 'HGNC ID', 'Approved Symbol', 'Approved Name', 'Status', 'Previous Symbols', 'Synonyms', 'Chromosome', 'Accession Numbers', 'RefSeq IDs', 'Entrez Gene ID(supplied by NCBI)', 'Ensembl ID(supplied by Ensembl)'
				entrezGeneID = row[9]
				status = row[3]
				approvedSymbol = row[1] # caution: invalid data possible (e.g. date)
				approvedName = row[2]
				
				toAdd = []
				if status == 'Approved':
					toAdd.append((entrezGeneID, approvedSymbol))
				elif status == 'Symbol Withdrawn':
					hgncIDs = [hgncID.strip() for hgncID in approvedName.replace('symbol withdrawn, see ','').split(',')] # more than 1 HGNC ID possible
					for hgncID in hgncIDs:
						toAdd.append((entrezGeneID, hgncID))
						
				for entrezGeneID, hgncSymbol in toAdd:
					if len(entrezGeneID) and len(hgncSymbol) and len(EntrezHGNCMap.query.filter_by(entrezGeneID = entrezGeneID, hgncSymbol = hgncSymbol).all()) == 0:
						db.session.add(EntrezHGNCMap(entrezGeneID = entrezGeneID, hgncSymbol = hgncSymbol))
		
		db.session.commit()
		
		updateStringEntrezHGNCMap()

def updateStringEntrezHGNCMap():
	for stringEntrez in StringEntrezMap.query.all():
		for entrezHGNC in EntrezHGNCMap.query.filter_by(entrezGeneID = stringEntrez.entrezGeneID).all():
			ensemblProteinID = stringEntrez.stringLocusID.replace('9606.','')
			hgncSymbol = entrezHGNC.hgncSymbol
			
			if len(EnsemblHGNCMap.query.filter_by(ensemblProteinID = ensemblProteinID, hgncSymbol = hgncSymbol).all()) == 0:
				db.session.add(EnsemblHGNCMap(ensemblProteinID = ensemblProteinID, hgncSymbol = hgncSymbol))
				
	db.session.commit()

def importDataFromFile(inputFile, format):
	if format == 'corpus':
		corpusImport(inputFile)
	elif format == 'xml':
		xmlImport(inputFile)
	elif format == 'ensemblHGNCMap':
		ensemblHGCNMapImport(inputFile)
	elif format == 'stringEntrezMap':
		stringEntrezMapImport(inputFile)
	elif format == 'entrezHGNCMap':
		entrezHGNCMapImport(inputFile)
	else:
		pass
	
def createBlock(blockLines):
	headLineComponents = blockLines[0].split("\t")
	
	ids = headLineComponents[1].split("__")
	pmid = ids[0]
	sentenceID = ids[1]
	sentence = headLineComponents[2]
	score = float(headLineComponents[3])
	
	# add Sentence
	s = Sentence(pubmedID = pmid, sentenceID = sentenceID, literal = sentence, score = score, grade = defaultGrade, comment = defaultComment)
	db.session.add(s)

	for line in blockLines[1:]:
		lineComponents = line.split("\t")
		
		# Possible forms:
		# PROTEIN_EXACT\tstart end\tword\tdatabase id
		# PROTEIN_GENIA\tstart end\tword\tPROTEIN_REFLECT\tstart end\tword\tdatabase id
		# PATTERN\tstart end\tinteraction_type

		try:
			kind = lineComponents[0]
		
			if kind == "PATTERN":
				start, end = startEnd(lineComponents[1])
				type = lineComponents[2]
				
				# add Interaction
				i = Interaction(type = type, start = start, end = end, sentence = s, grade = defaultGrade, comment = defaultComment)
				db.session.add(i)
			else:
				type, software = typeSoftware(kind.replace("GO_PROCESS", "GO-PROCESS").replace("CHEM", "CHEMICAL"))

				if type.upper() != "PROTEIN" or software.upper() == "EXACT":
					start, end = startEnd(lineComponents[1])
					name = lineComponents[2]
					databaseID = lineComponents[3]
					
					# add Entity
					e = Entity(type = type, software = software, name = name, databaseID = databaseID, start = start, end = end, sentence = s, grade = defaultGrade, comment = defaultComment)
					db.session.add(e)
				else:
					# partial overlap
					databaseID = lineComponents[6]
				
					type1, software1 = typeSoftware(lineComponents[0])
					start1, end1 = startEnd(lineComponents[1])
					name1 = lineComponents[2]
				
					# add Entity
					e1 = Entity(type = type1, software = software1, name = name1, databaseID = databaseID, start = start1, end = end1, sentence = s, grade = defaultGrade, comment = defaultComment)
					db.session.add(e1)
				
					type2, software2 = typeSoftware(lineComponents[3])
					start2, end2 = startEnd(lineComponents[4])
					name2 = lineComponents[5]
				
					# add Entity
					e2 = Entity(type = type2, software = software2, name = name2, databaseID = databaseID, start = start2, end = end2, sentence = s, grade = defaultGrade, comment = defaultComment)
					db.session.add(e2)

		except:
			raise "Error: {}\n\nLine Components: {}".format(sys.exc_info()[0], lineComponents)
		
	db.session.commit()

def startEnd(s):
	se = s.split(" ")
	return int(se[0]), int(se[1])

def typeSoftware(s):
	ts = s.split("_")
	return ts[0].lower().title(), (ts[1].lower().title() if len(ts) == 2 else "")

def decode(s):
	return s.encode('utf-8','ignore').decode('ascii','ignore').strip()
