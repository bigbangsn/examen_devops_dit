from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
class Personne(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tache = db.relationship('Tache', backref='personne', lazy=True)

class Tache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    personne_id = db.Column(db.Integer, db.ForeignKey('personne.id'), nullable=False)