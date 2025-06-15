from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

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
    submit = SubmitField('Enregistrer')