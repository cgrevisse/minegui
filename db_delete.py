from app.models import *
from app import db

Sentence.query.delete()
Entity.query.delete()
Interaction.query.delete()
EnsemblHGNCMap.query.delete()
OntologyAnnotation.query.delete()
db.session.commit()