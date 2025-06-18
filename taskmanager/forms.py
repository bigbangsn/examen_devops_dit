from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateField, HiddenField, BooleanField, FileField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional, Regexp, Email
import re
from markupsafe import escape
from datetime import datetime
from typing import Optional as OptionalType, List, Dict, Any
from flask import session
from taskmanager.models import UserRole, Personne

class EnregistreForm(FlaskForm):
    """Registration form for new users."""

    nom = StringField('Nom d\'utilisateur', validators=[
        DataRequired(message="Le nom d'utilisateur est requis"),
        Length(min=3, max=50, message="Le nom d'utilisateur doit contenir entre 3 et 50 caractères"),
        Regexp(r'^[A-Za-z0-9_-]+$', message="Le nom d'utilisateur ne peut contenir que des lettres, chiffres, tirets et underscores")
    ])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message="Le mot de passe est requis"),
        Length(min=8, message="Le mot de passe doit contenir au moins 8 caractères")
    ])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(message="La confirmation du mot de passe est requise"),
        EqualTo('password', message="Les mots de passe doivent correspondre")
    ])
    submit = SubmitField('S\'inscrire')

    def validate_password(self, password) -> OptionalType[ValidationError]:
        """Validate password complexity."""
        if not re.search(r'[A-Z]', password.data):
            raise ValidationError('Le mot de passe doit contenir au moins une lettre majuscule.')
        if not re.search(r'[a-z]', password.data):
            raise ValidationError('Le mot de passe doit contenir au moins une lettre minuscule.')
        if not re.search(r'[0-9]', password.data):
            raise ValidationError('Le mot de passe doit contenir au moins un chiffre.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password.data):
            raise ValidationError('Le mot de passe doit contenir au moins un caractère spécial.')

    def validate_nom(self, nom) -> OptionalType[ValidationError]:
        """Validate that the username is not already taken and sanitize it."""
        # Sanitize the username
        sanitized_username = escape(nom.data.strip())
        if sanitized_username != nom.data:
            raise ValidationError('Le nom d\'utilisateur contient des caractères non autorisés.')

        from taskmanager.models import Personne
        personne = Personne.query.filter_by(nom=sanitized_username).first()
        if personne:
            raise ValidationError('Ce nom d\'utilisateur est déjà pris. Veuillez en choisir un autre.')


class ConnexionForm(FlaskForm):
    """Login form for existing users."""

    nom = StringField('Nom d\'utilisateur', validators=[
        DataRequired(message="Le nom d'utilisateur est requis"),
        Regexp(r'^[A-Za-z0-9_-]+$', message="Le nom d'utilisateur ne peut contenir que des lettres, chiffres, tirets et underscores")
    ])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message="Le mot de passe est requis")
    ])
    submit = SubmitField('Connexion')

    def validate_nom(self, nom) -> OptionalType[ValidationError]:
        """Sanitize the username input."""
        # Sanitize the username
        sanitized_username = escape(nom.data.strip())
        if sanitized_username != nom.data:
            raise ValidationError('Le nom d\'utilisateur contient des caractères non autorisés.')

class CategorieForm(FlaskForm):
    """Form for creating and editing categories."""

    id = HiddenField('ID')
    nom = StringField('Nom de la catégorie', validators=[
        DataRequired(message="Le nom est requis"),
        Length(max=50, message="Le nom ne peut pas dépasser 50 caractères")
    ])
    description = StringField('Description', validators=[
        Optional(),
        Length(max=200, message="La description ne peut pas dépasser 200 caractères")
    ])
    couleur = StringField('Couleur', validators=[
        DataRequired(message="La couleur est requise"),
        Regexp(r'^#[0-9A-Fa-f]{6}$', message="La couleur doit être au format hexadécimal (ex: #007bff)")
    ])
    submit = SubmitField('Enregistrer')

    def __init__(self, *args, **kwargs):
        """Initialize the form with dynamic validation."""
        super(CategorieForm, self).__init__(*args, **kwargs)

    def validate_nom(self, nom) -> OptionalType[ValidationError]:
        """Validate that the category name is unique for this user and sanitize it."""
        # Sanitize the category name
        sanitized_name = escape(nom.data.strip())
        if sanitized_name != nom.data:
            raise ValidationError('Le nom de la catégorie contient des caractères non autorisés.')

        from taskmanager.models import Categorie
        personne_id = session.get('personne_id')
        if not personne_id:
            return

        # Check if a category with this name already exists for this user
        # Exclude the current category when editing
        query = Categorie.query.filter_by(nom=sanitized_name, personne_id=personne_id)
        if self.id and self.id.data:  # If editing an existing category
            query = query.filter(Categorie.id != int(self.id.data))

        if query.first():
            raise ValidationError('Une catégorie avec ce nom existe déjà.')

    def validate_description(self, description) -> OptionalType[ValidationError]:
        """Sanitize the description input."""
        if description.data:
            sanitized_description = escape(description.data.strip())
            if sanitized_description != description.data:
                raise ValidationError('La description contient des caractères non autorisés.')


class TacheForm(FlaskForm):
    """Form for creating and editing tasks."""

    titre = StringField('Titre de la tâche', validators=[
        DataRequired(message="Le titre est requis"),
        Length(max=200, message="Le titre ne peut pas dépasser 200 caractères")
    ])
    description = TextAreaField('Description', validators=[
        Optional()
    ])
    status = SelectField('Statut', choices=[
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée')
    ], validators=[DataRequired(message="Le statut est requis")])
    priority = SelectField('Priorité', choices=[
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute')
    ], validators=[DataRequired(message="La priorité est requise")])
    categorie_id = SelectField('Catégorie', coerce=int, validators=[
        Optional()
    ])
    due_date = DateField('Date d\'échéance', format='%Y-%m-%d', validators=[
        Optional()
    ])
    submit = SubmitField('Enregistrer')

    def __init__(self, *args, **kwargs):
        """Initialize the form with dynamic category choices."""
        super(TacheForm, self).__init__(*args, **kwargs)
        personne_id = session.get('personne_id')
        if personne_id:
            from taskmanager.models import Categorie
            categories = Categorie.query.filter_by(personne_id=personne_id).all()
            self.categorie_id.choices = [(0, 'Aucune catégorie')] + [(c.id, c.nom) for c in categories]

    def validate_due_date(self, due_date) -> OptionalType[ValidationError]:
        """Validate that the due date is not in the past."""
        if due_date.data and due_date.data < datetime.now().date():
            raise ValidationError('La date d\'échéance ne peut pas être dans le passé.')

    def validate_titre(self, titre) -> OptionalType[ValidationError]:
        """Sanitize the title input."""
        sanitized_title = escape(titre.data.strip())
        if sanitized_title != titre.data:
            raise ValidationError('Le titre contient des caractères non autorisés.')

    def validate_description(self, description) -> OptionalType[ValidationError]:
        """Sanitize the description input."""
        if description.data:
            sanitized_description = escape(description.data.strip())
            if sanitized_description != description.data:
                raise ValidationError('La description contient des caractères non autorisés.')
