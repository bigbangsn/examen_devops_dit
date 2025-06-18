from datetime import datetime
from taskmanager import db
from typing import List, Optional
from enum import Enum

class UserRole(str, Enum):
    """Enum for user roles."""
    USER = "user"
    ADMIN = "admin"

class Personne(db.Model):
    """User model representing a person in the system."""

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.USER)
    email = db.Column(db.String(150), unique=True, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(200), nullable=True, default='default.jpg')
    notification_preferences = db.Column(db.Boolean, default=True)  # For email notifications
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    taches = db.relationship('Tache', backref='personne', lazy=True, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<Personne {self.nom}>"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN

class Categorie(db.Model):
    """Category model for task categorization."""

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    couleur = db.Column(db.String(20), default='#007bff', nullable=False)  # Default color (blue)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    personne_id = db.Column(db.Integer, db.ForeignKey('personne.id'), nullable=False)

    # Relationships
    taches = db.relationship('Tache', backref='categorie', lazy=True)

    def __repr__(self) -> str:
        """String representation of the category."""
        return f"<Categorie {self.nom}>"


class Tache(db.Model):
    """Task model representing a task in the system."""

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, in_progress, completed
    priority = db.Column(db.String(20), default='medium', nullable=False)  # low, medium, high
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)  # Soft delete flag

    # Foreign keys
    personne_id = db.Column(db.Integer, db.ForeignKey('personne.id'), nullable=False)
    categorie_id = db.Column(db.Integer, db.ForeignKey('categorie.id'), nullable=True)

    def __repr__(self) -> str:
        """String representation of the task."""
        return f"<Tache {self.titre}>"

    @classmethod
    def get_active_tasks(cls, personne_id: int) -> List['Tache']:
        """Get all active (not deleted) tasks for a user."""
        return cls.query.filter_by(personne_id=personne_id, is_deleted=False).all()

    def soft_delete(self) -> None:
        """Mark the task as deleted without removing it from the database."""
        self.is_deleted = True
        db.session.commit()
