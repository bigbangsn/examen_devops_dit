from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Optional

class EnregistreForm(FlaskForm):
    nom = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=4)])
    submit = SubmitField('S\'inscrire')

class ConnexionForm(FlaskForm):
    nom = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Connexion')

class TacheForm(FlaskForm):
    titre = StringField('Titre de la tâche', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    status = SelectField('Statut', choices=[
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée')
    ], validators=[DataRequired()])
    priority = SelectField('Priorité', choices=[
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute')
    ], validators=[DataRequired()])
    due_date = DateField('Date d\'échéance', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Enregistrer')
