from flask import render_template, redirect, url_for, session, flash, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from taskmanager import db, limiter
from taskmanager.models import Personne, UserRole
from taskmanager.forms import EnregistreForm, ConnexionForm
from taskmanager.auth import auth_bp
from taskmanager.session_utils import regenerate_session
from functools import wraps
from typing import Callable, Any, List, Dict, Union
from datetime import datetime
from markupsafe import escape

def login_required(f: Callable) -> Callable:
    """
    Decorator to ensure a route is only accessible to logged-in users.

    Args:
        f: The function to decorate

    Returns:
        The decorated function
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'personne_id' not in session:
            flash("Vous devez être connecté pour accéder à cette page.", "danger")
            return redirect(url_for('auth.connexion'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f: Callable) -> Callable:
    """
    Decorator to ensure a route is only accessible to admin users.

    This decorator should be applied after the login_required decorator.

    Args:
        f: The function to decorate

    Returns:
        The decorated function
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # First ensure user is logged in
        if 'personne_id' not in session:
            flash("Vous devez être connecté pour accéder à cette page.", "danger")
            return redirect(url_for('auth.connexion'))

        # Then check if user is admin
        personne = Personne.query.get(session['personne_id'])
        if not personne or not personne.is_admin:
            current_app.logger.warning(
                f"Tentative d'accès à une page admin par l'utilisateur {personne.nom if personne else 'inconnu'}"
            )
            flash("Vous n'avez pas les permissions nécessaires pour accéder à cette page.", "danger")
            return redirect(url_for('tasks.liste'))

        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/enregistrer', methods=['GET', 'POST'])
def enregistrer():
    """Route for user registration."""
    form = EnregistreForm()
    if form.validate_on_submit():
        try:
            # Use sanitized data
            sanitized_nom = escape(form.nom.data.strip())
            hashed_pw = generate_password_hash(form.password.data)

            # Check if user already exists
            existing_user = Personne.query.filter_by(nom=sanitized_nom).first()
            if existing_user:
                flash(f"Le nom d'utilisateur '{sanitized_nom}' est déjà pris.", "danger")
                current_app.logger.warning(f"Tentative de création d'un utilisateur avec un nom déjà existant: {sanitized_nom}")
                return render_template('enregistrer.html', form=form)

            # Create new user
            personne = Personne(nom=sanitized_nom, password=hashed_pw)
            db.session.add(personne)
            db.session.commit()

            current_app.logger.info(f"Nouvel utilisateur créé: {sanitized_nom}")
            flash("Compte créé ! Connectez-vous.", "success")
            return redirect(url_for('auth.connexion'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la création de l'utilisateur: {str(e)}")
            flash("Une erreur est survenue lors de la création du compte. Veuillez réessayer.", "danger")
    return render_template('enregistrer.html', form=form)

@auth_bp.route('/connexion', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def connexion():
    """Route for user login with rate limiting (5 attempts per minute)."""
    if 'personne_id' in session:
        return redirect(url_for('tasks.liste'))

    form = ConnexionForm()
    if form.validate_on_submit():
        # Use sanitized data
        sanitized_nom = escape(form.nom.data.strip())
        personne = Personne.query.filter_by(nom=sanitized_nom).first()
        if personne and check_password_hash(personne.password, form.password.data):
            # Clear the session and regenerate session ID for security
            session.clear()

            # Set session to permanent and mark login time
            session.permanent = True
            session['personne_id'] = personne.id
            session['login_time'] = datetime.utcnow().timestamp()

            # Regenerate session ID for security
            regenerate_session()

            current_app.logger.info(f"Utilisateur connecté: {sanitized_nom}")
            flash(f"Bienvenue, {personne.nom}!", "success")
            return redirect(url_for('tasks.liste'))
        flash("Identifiants invalides.", "danger")
        current_app.logger.warning(f"Tentative de connexion échouée pour: {sanitized_nom}")
    return render_template('connexion.html', form=form)

@auth_bp.route('/deconnecter')
def deconnecter():
    """Route for user logout."""
    if 'personne_id' in session:
        current_app.logger.info(f"Utilisateur déconnecté: {Personne.query.get(session['personne_id']).nom}")
    session.pop('personne_id', None)
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for('auth.connexion'))

@auth_bp.route('/')
def accueil():
    """Route for the home page, redirects to tasks if logged in, otherwise to login."""
    if 'personne_id' in session:
        return redirect(url_for('tasks.liste'))
    return redirect(url_for('auth.connexion'))
