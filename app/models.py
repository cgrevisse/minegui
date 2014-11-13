from app import db

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
    
    type = db.Column(db.Enum("Protein", "Disease", "Biological Process", "Chemical"))
    software = db.Column(db.Enum("Genia", "Reflect", "Exact"))
    name = db.Column(db.String(100))
    databaseID = db.Column(db.String(50))
    
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentence.id'))
    
    def __repr__(self):
        return str(self.serialize)
    
    @property
    def serialize(self):
        return {
            'type': self.type,
            'name': self.name,
            'software': self.software,
            'databaseID': self.databaseID,
            'start': self.start,
            'end': self.end,
            'grade': self.grade,
            'comment': self.comment,
            'sentence_id': self.sentence_id
        }
    
class Interaction(Keyword):
    __tablename__ = "interaction"
    
    type = db.Column(db.String(100))
    
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentence.id'))
    
    def __repr__(self):
        return str(self.serialize)
    
    @property
    def serialize(self):
        return {
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
    entities = db.relationship('Entity', backref = 'sentence')
    interactions = db.relationship('Interaction', backref = 'sentence') 
    
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
