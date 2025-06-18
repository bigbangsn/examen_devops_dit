from flask import render_template, redirect, url_for, session, request, current_app
from taskmanager import db
from taskmanager.models import Categorie, Personne
from taskmanager.forms import CategorieForm
from taskmanager.categories import categories_bp
from taskmanager.auth.routes import login_required, admin_required
from taskmanager.utils import log_and_flash
from taskmanager.exceptions import AuthorizationError, ResourceNotFoundError
from datetime import datetime
from typing import List
from markupsafe import escape

@categories_bp.route('/')
@login_required
def liste():
    """Route for listing all categories for the current user."""
    personne_id = session.get('personne_id')
    categories = Categorie.query.filter_by(personne_id=personne_id).all()

    log_and_flash(f"Affichage de {len(categories)} catégories pour l'utilisateur {personne_id}", 
                 level="debug", flash_category=None)
    return render_template('categories/liste.html', categories=categories)

@categories_bp.route('/admin/all')
@login_required
@admin_required
def admin_liste():
    """Admin route for listing all categories across all users."""
    categories = Categorie.query.all()
    users = Personne.query.all()

    # Create a dictionary mapping user IDs to names for display
    user_names = {user.id: user.nom for user in users}

    log_and_flash(f"Affichage de toutes les catégories ({len(categories)}) pour l'administrateur", 
                 level="debug", flash_category=None)
    return render_template('categories/admin_liste.html', categories=categories, user_names=user_names)

@categories_bp.route('/nouvelle', methods=['GET', 'POST'])
@login_required
def nouvelle():
    """Route for creating a new category."""
    form = CategorieForm()
    if form.validate_on_submit():
        # Use sanitized data
        sanitized_nom = escape(form.nom.data.strip())
        sanitized_description = escape(form.description.data.strip()) if form.description.data else None

        categorie = Categorie(
            nom=sanitized_nom,
            description=sanitized_description,
            couleur=form.couleur.data,
            personne_id=session['personne_id']
        )
        db.session.add(categorie)
        db.session.commit()
        log_and_flash(f"Nouvelle catégorie créée: {categorie.nom}", level="info")
        return redirect(url_for('categories.liste'))
    return render_template('categories/ajouter_editer.html', form=form, title="Nouvelle Catégorie")

@categories_bp.route('/editer/<int:categorie_id>', methods=['GET', 'POST'])
@login_required
def editer(categorie_id: int):
    """Route for editing an existing category."""
    try:
        categorie = Categorie.query.get_or_404(categorie_id)

        # Check if the category belongs to the current user
        if categorie.personne_id != session['personne_id']:
            raise AuthorizationError("Vous n'êtes pas autorisé à modifier cette catégorie")

        form = CategorieForm()
        if form.validate_on_submit():
            # Use sanitized data
            sanitized_nom = escape(form.nom.data.strip())
            sanitized_description = escape(form.description.data.strip()) if form.description.data else None

            categorie.nom = sanitized_nom
            categorie.description = sanitized_description
            categorie.couleur = form.couleur.data
            categorie.updated_at = datetime.utcnow()
            db.session.commit()
            log_and_flash(f"Catégorie mise à jour: {categorie.nom}")
            return redirect(url_for('categories.liste'))

        # Pre-populate form with existing category data
        if request.method == 'GET':
            form.id.data = categorie.id
            form.nom.data = categorie.nom
            form.description.data = categorie.description
            form.couleur.data = categorie.couleur

        return render_template('categories/ajouter_editer.html', form=form, title="Modifier Catégorie")

    except (ResourceNotFoundError, AuthorizationError) as e:
        log_and_flash(e.message, level="warning", flash_category="danger")
        return redirect(url_for('categories.liste'))

@categories_bp.route('/admin/editer/<int:categorie_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_editer(categorie_id: int):
    """Admin route for editing any category regardless of ownership."""
    try:
        categorie = Categorie.query.get_or_404(categorie_id)
        owner = Personne.query.get(categorie.personne_id)

        form = CategorieForm()
        if form.validate_on_submit():
            # Use sanitized data
            sanitized_nom = escape(form.nom.data.strip())
            sanitized_description = escape(form.description.data.strip()) if form.description.data else None

            categorie.nom = sanitized_nom
            categorie.description = sanitized_description
            categorie.couleur = form.couleur.data
            categorie.updated_at = datetime.utcnow()
            db.session.commit()
            log_and_flash(f"Catégorie mise à jour par admin: {categorie.nom} (propriétaire: {owner.nom})")
            return redirect(url_for('categories.admin_liste'))

        # Pre-populate form with existing category data
        if request.method == 'GET':
            form.id.data = categorie.id
            form.nom.data = categorie.nom
            form.description.data = categorie.description
            form.couleur.data = categorie.couleur

        return render_template('categories/admin_editer.html', form=form, categorie=categorie, owner=owner)

    except (ResourceNotFoundError, AuthorizationError) as e:
        log_and_flash(e.message, level="warning", flash_category="danger")
        return redirect(url_for('categories.admin_liste'))

@categories_bp.route('/admin/supprimer/<int:categorie_id>')
@login_required
@admin_required
def admin_supprimer(categorie_id: int):
    """Admin route for deleting any category regardless of ownership."""
    try:
        categorie = Categorie.query.get_or_404(categorie_id)
        owner = Personne.query.get(categorie.personne_id)

        # Remove category from tasks
        for tache in categorie.taches:
            tache.categorie_id = None

        # Delete the category
        nom_categorie = categorie.nom
        nom_owner = owner.nom
        db.session.delete(categorie)
        db.session.commit()
        log_and_flash(f"Catégorie supprimée par admin: {nom_categorie} (propriétaire: {nom_owner})")
        return redirect(url_for('categories.admin_liste'))

    except (ResourceNotFoundError, AuthorizationError) as e:
        log_and_flash(e.message, level="warning", flash_category="danger")
        return redirect(url_for('categories.admin_liste'))

@categories_bp.route('/supprimer/<int:categorie_id>')
@login_required
def supprimer(categorie_id: int):
    """Route for deleting a category."""
    try:
        categorie = Categorie.query.get_or_404(categorie_id)

        # Check if the category belongs to the current user
        if categorie.personne_id != session['personne_id']:
            raise AuthorizationError("Vous n'êtes pas autorisé à supprimer cette catégorie")

        # Remove category from tasks
        for tache in categorie.taches:
            tache.categorie_id = None

        # Delete the category
        db.session.delete(categorie)
        db.session.commit()
        log_and_flash(f"Catégorie supprimée: {categorie.nom}")
        return redirect(url_for('categories.liste'))

    except (ResourceNotFoundError, AuthorizationError) as e:
        log_and_flash(e.message, level="warning", flash_category="danger")
        return redirect(url_for('categories.liste'))
