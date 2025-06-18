from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, FileField
from wtforms.validators import Email, Length, EqualTo, ValidationError, Optional
import re
from markupsafe import escape
from typing import Optional as OptionalType
from taskmanager.models import Personne

class ProfileForm(FlaskForm):
    """Form for editing user profile information."""
    
    email = StringField('Email', validators=[
        Optional(),
        Email(message="Veuillez entrer une adresse email valide"),
        Length(max=150, message="L'email ne peut pas dépasser 150 caractères")
    ])
    bio = TextAreaField('Biographie', validators=[
        Optional(),
        Length(max=500, message="La biographie ne peut pas dépasser 500 caractères")
    ])
    profile_picture = FileField('Photo de profil', validators=[
        Optional()
    ])
    current_password = PasswordField('Mot de passe actuel', validators=[
        Optional()
    ])
    new_password = PasswordField('Nouveau mot de passe', validators=[
        Optional(),
        Length(min=8, message="Le mot de passe doit contenir au moins 8 caractères")
    ])
    confirm_new_password = PasswordField('Confirmer le nouveau mot de passe', validators=[
        Optional(),
        EqualTo('new_password', message="Les mots de passe doivent correspondre")
    ])
    notification_preferences = BooleanField('Recevoir des notifications par email', default=True)
    submit = SubmitField('Mettre à jour le profil')
    
    def __init__(self, user_id=None, *args, **kwargs):
        """Initialize the form with user data."""
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.user_id = user_id
    
    def validate_email(self, email) -> OptionalType[ValidationError]:
        """Validate that the email is unique and sanitize it."""
        if not email.data:
            return
            
        # Sanitize the email
        sanitized_email = escape(email.data.strip())
        if sanitized_email != email.data:
            raise ValidationError('L\'email contient des caractères non autorisés.')
        
        # Check if email is already taken by another user
        existing_user = Personne.query.filter_by(email=sanitized_email).first()
        if existing_user and existing_user.id != self.user_id:
            raise ValidationError('Cette adresse email est déjà utilisée par un autre compte.')
    
    def validate_bio(self, bio) -> OptionalType[ValidationError]:
        """Sanitize the bio input."""
        if bio.data:
            sanitized_bio = escape(bio.data.strip())
            if sanitized_bio != bio.data:
                raise ValidationError('La biographie contient des caractères non autorisés.')
    
    def validate_new_password(self, new_password) -> OptionalType[ValidationError]:
        """Validate password complexity if provided."""
        if new_password.data:
            if not re.search(r'[A-Z]', new_password.data):
                raise ValidationError('Le mot de passe doit contenir au moins une lettre majuscule.')
            if not re.search(r'[a-z]', new_password.data):
                raise ValidationError('Le mot de passe doit contenir au moins une lettre minuscule.')
            if not re.search(r'[0-9]', new_password.data):
                raise ValidationError('Le mot de passe doit contenir au moins un chiffre.')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password.data):
                raise ValidationError('Le mot de passe doit contenir au moins un caractère spécial.')