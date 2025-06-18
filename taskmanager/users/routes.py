from flask import render_template, redirect, url_for, flash, request, current_app, session
from werkzeug.security import generate_password_hash, check_password_hash
from taskmanager import db
from taskmanager.models import Personne, UserRole
from taskmanager.users import users_bp
from taskmanager.auth.routes import login_required, admin_required
from taskmanager.utils import log_and_flash
from taskmanager.exceptions import AuthorizationError, ResourceNotFoundError
from taskmanager.profile_form import ProfileForm
from datetime import datetime
from typing import List
from markupsafe import escape
import os
from werkzeug.utils import secure_filename

@users_bp.route('/admin/list')
@login_required
@admin_required
def admin_liste():
    """Admin route for listing all users."""
    users = Personne.query.all()
    log_and_flash(f"Affichage de tous les utilisateurs ({len(users)}) pour l'administrateur", 
                 level="debug", flash_category=None)
    return render_template('users/admin_liste.html', users=users, roles=UserRole)

@users_bp.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit(user_id: int):
    """Admin route for editing a user."""
    try:
        user = Personne.query.get_or_404(user_id)

        if request.method == 'POST':
            # Get form data
            nom = escape(request.form.get('nom', '').strip())
            role = request.form.get('role')

            # Validate data
            if not nom:
                flash("Le nom est requis.", "danger")
                return redirect(url_for('users.admin_edit', user_id=user_id))

            if role not in [r.value for r in UserRole]:
                flash("Rôle invalide.", "danger")
                return redirect(url_for('users.admin_edit', user_id=user_id))

            # Check if name is already taken by another user
            existing_user = Personne.query.filter_by(nom=nom).first()
            if existing_user and existing_user.id != user_id:
                flash("Ce nom est déjà utilisé.", "danger")
                return redirect(url_for('users.admin_edit', user_id=user_id))

            # Update user
            user.nom = nom
            user.role = role
            user.updated_at = datetime.utcnow()
            db.session.commit()

            log_and_flash(f"Utilisateur mis à jour: {user.nom}", level="info")
            return redirect(url_for('users.admin_liste'))

        return render_template('users/admin_edit.html', user=user, roles=UserRole)

    except Exception as e:
        log_and_flash(str(e), level="error", flash_category="danger")
        return redirect(url_for('users.admin_liste'))

@users_bp.route('/admin/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create():
    """Admin route for creating a new user."""
    if request.method == 'POST':
        # Get form data
        nom = escape(request.form.get('nom', '').strip())
        password = request.form.get('password')
        role = request.form.get('role')

        # Validate data
        if not nom or not password:
            flash("Le nom et le mot de passe sont requis.", "danger")
            return redirect(url_for('users.admin_create'))

        if role not in [r.value for r in UserRole]:
            flash("Rôle invalide.", "danger")
            return redirect(url_for('users.admin_create'))

        # Check if name is already taken
        if Personne.query.filter_by(nom=nom).first():
            flash("Ce nom est déjà utilisé.", "danger")
            return redirect(url_for('users.admin_create'))

        # Create user
        hashed_pw = generate_password_hash(password)
        user = Personne(nom=nom, password=hashed_pw, role=role)
        db.session.add(user)
        db.session.commit()

        log_and_flash(f"Nouvel utilisateur créé: {user.nom}", level="info")
        return redirect(url_for('users.admin_liste'))

    return render_template('users/admin_create.html', roles=UserRole)

@users_bp.route('/admin/delete/<int:user_id>')
@login_required
@admin_required
def admin_delete(user_id: int):
    """Admin route for deleting a user."""
    try:
        user = Personne.query.get_or_404(user_id)

        # Prevent deleting yourself
        if user.id == request.cookies.get('personne_id'):
            flash("Vous ne pouvez pas supprimer votre propre compte.", "danger")
            return redirect(url_for('users.admin_liste'))

        nom_user = user.nom
        db.session.delete(user)
        db.session.commit()

        log_and_flash(f"Utilisateur supprimé: {nom_user}", level="info")
        return redirect(url_for('users.admin_liste'))

    except Exception as e:
        log_and_flash(str(e), level="error", flash_category="danger")
        return redirect(url_for('users.admin_liste'))
