from app.models import Sentence, Entity, Interaction
from app import db

Sentence.query.delete()
Entity.query.delete()
Interaction.query.delete()
db.session.commit()
