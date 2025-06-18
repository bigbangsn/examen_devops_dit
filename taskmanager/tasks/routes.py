from flask import render_template, redirect, url_for, session, request, current_app
from taskmanager import db
from taskmanager.models import Tache, Personne
from taskmanager.forms import TacheForm
from taskmanager.tasks import tasks_bp
from taskmanager.auth.routes import login_required, admin_required
from taskmanager.utils import (
    get_task_by_id, 
    verify_task_ownership, 
    log_and_flash, 
    populate_task_from_form, 
    save_task,
    get_tasks_optimized,
    get_admin_tasks_optimized
)
from taskmanager.exceptions import AuthorizationError, ResourceNotFoundError
from datetime import datetime
from typing import List

@tasks_bp.route('/')
@login_required
def liste():
    """Route for listing all tasks for the current user with pagination."""
    personne_id = session.get('personne_id')

    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Get filter parameters
    status = request.args.get('status')
    priority = request.args.get('priority')
    category_id = request.args.get('category_id')
    if category_id and category_id.isdigit():
        category_id = int(category_id)

    # Get sort parameters
    sort_by = request.args.get('sort_by', 'due_date')
    sort_dir = request.args.get('sort_dir', 'asc')

    # Get tasks with pagination and filtering
    taches, total_count, total_pages = get_tasks_optimized(
        user_id=personne_id,
        page=page,
        per_page=per_page,
        status=status,
        priority=priority,
        category_id=category_id,
        sort_by=sort_by,
        sort_dir=sort_dir
    )

    # Get categories for filtering UI
    from taskmanager.models import Categorie
    categories = Categorie.query.filter_by(personne_id=personne_id).all()

    log_and_flash(f"Affichage de {len(taches)} tâches sur {total_count} pour l'utilisateur {personne_id} (page {page}/{total_pages})", 
                 level="debug", flash_category=None)

    return render_template(
        'taches.html', 
        taches=taches, 
        categories=categories,
        pagination={
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages
        },
        filters={
            'status': status,
            'priority': priority,
            'category_id': category_id,
            'sort_by': sort_by,
            'sort_dir': sort_dir
        }
    )

@tasks_bp.route('/admin/all')
@login_required
@admin_required
def admin_liste():
    """Admin route for listing all tasks across all users with pagination."""
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Get filter parameters
    status = request.args.get('status')
    priority = request.args.get('priority')
    user_id = request.args.get('user_id')
    if user_id and user_id.isdigit():
        user_id = int(user_id)
    category_id = request.args.get('category_id')
    if category_id and category_id.isdigit():
        category_id = int(category_id)

    # Get sort parameters
    sort_by = request.args.get('sort_by', 'due_date')
    sort_dir = request.args.get('sort_dir', 'asc')

    # Get tasks with pagination and filtering
    taches, total_count, total_pages = get_admin_tasks_optimized(
        page=page,
        per_page=per_page,
        status=status,
        priority=priority,
        user_id=user_id,
        category_id=category_id,
        sort_by=sort_by,
        sort_dir=sort_dir
    )

    # Get all users for filtering UI and mapping user IDs to names
    users = Personne.query.all()
    user_names = {user.id: user.nom for user in users}

    # Get all categories for filtering UI
    from taskmanager.models import Categorie
    categories = Categorie.query.all()

    log_and_flash(f"Affichage de {len(taches)} tâches sur {total_count} pour l'administrateur (page {page}/{total_pages})", 
                 level="debug", flash_category=None)

    return render_template(
        'admin_taches.html', 
        taches=taches, 
        user_names=user_names, 
        users=users, 
        categories=categories,
        pagination={
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages
        },
        filters={
            'status': status,
            'priority': priority,
            'user_id': user_id,
            'category_id': category_id,
            'sort_by': sort_by,
            'sort_dir': sort_dir
        }
    )

@tasks_bp.route('/nouvelle', methods=['GET', 'POST'])
@login_required
def nouvelle():
    """Route for creating a new task."""
    form = TacheForm()
    if form.validate_on_submit():
        tache = Tache(personne_id=session['personne_id'])
        populate_task_from_form(tache, {
            'titre': form.titre.data,
            'description': form.description.data,
            'status': form.status.data,
            'priority': form.priority.data,
            'due_date': form.due_date.data,
            'categorie_id': form.categorie_id.data
        })
        save_task(tache, is_new=True)
        log_and_flash(f"Nouvelle tâche créée: {tache.titre}", level="info")
        return redirect(url_for('tasks.liste'))
    return render_template('ajouter_editer_tache.html', form=form, title="Nouvelle Tâche")

@tasks_bp.route('/editer/<int:tache_id>', methods=['GET', 'POST'])
@login_required
def editer(tache_id: int):
    """Route for editing an existing task."""
    try:
        tache = get_task_by_id(tache_id)
        verify_task_ownership(tache)

        form = TacheForm()
        if form.validate_on_submit():
            populate_task_from_form(tache, {
                'titre': form.titre.data,
                'description': form.description.data,
                'status': form.status.data,
                'priority': form.priority.data,
                'due_date': form.due_date.data,
                'categorie_id': form.categorie_id.data
            })
            tache.updated_at = datetime.utcnow()
            save_task(tache)
            log_and_flash(f"Tâche mise à jour: {tache.titre}")
            return redirect(url_for('tasks.liste'))

        # Pre-populate form with existing task data
        if request.method == 'GET':
            form.titre.data = tache.titre
            form.description.data = tache.description
            form.status.data = tache.status
            form.priority.data = tache.priority
            form.due_date.data = tache.due_date

        return render_template('ajouter_editer_tache.html', form=form, title="Modifier Tâche")

    except (ResourceNotFoundError, AuthorizationError) as e:
        log_and_flash(e.message, level="warning", flash_category="danger")
        return redirect(url_for('tasks.liste'))

@tasks_bp.route('/supprimer/<int:tache_id>')
@login_required
def supprimer(tache_id: int):
    """Route for deleting a task (soft delete)."""
    try:
        tache = get_task_by_id(tache_id)
        verify_task_ownership(tache)

        # Soft delete the task
        tache.soft_delete()
        log_and_flash(f"Tâche supprimée: {tache.titre}")
        return redirect(url_for('tasks.liste'))

    except (ResourceNotFoundError, AuthorizationError) as e:
        log_and_flash(e.message, level="warning", flash_category="danger")
        return redirect(url_for('tasks.liste'))

@tasks_bp.route('/admin/editer/<int:tache_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_editer(tache_id: int):
    """Admin route for editing any task regardless of ownership."""
    try:
        tache = get_task_by_id(tache_id)
        owner = Personne.query.get(tache.personne_id)

        form = TacheForm()
        if form.validate_on_submit():
            populate_task_from_form(tache, {
                'titre': form.titre.data,
                'description': form.description.data,
                'status': form.status.data,
                'priority': form.priority.data,
                'due_date': form.due_date.data,
                'categorie_id': form.categorie_id.data
            })
            tache.updated_at = datetime.utcnow()
            save_task(tache)
            log_and_flash(f"Tâche mise à jour par admin: {tache.titre} (propriétaire: {owner.nom})")
            return redirect(url_for('tasks.admin_liste'))

        # Pre-populate form with existing task data
        if request.method == 'GET':
            form.titre.data = tache.titre
            form.description.data = tache.description
            form.status.data = tache.status
            form.priority.data = tache.priority
            form.due_date.data = tache.due_date

        return render_template('admin_editer_tache.html', form=form, tache=tache, owner=owner)

    except (ResourceNotFoundError, AuthorizationError) as e:
        log_and_flash(e.message, level="warning", flash_category="danger")
        return redirect(url_for('tasks.admin_liste'))

@tasks_bp.route('/admin/supprimer/<int:tache_id>')
@login_required
@admin_required
def admin_supprimer(tache_id: int):
    """Admin route for deleting any task regardless of ownership."""
    try:
        tache = get_task_by_id(tache_id)
        owner = Personne.query.get(tache.personne_id)

        # Soft delete the task
        tache.soft_delete()
        log_and_flash(f"Tâche supprimée par admin: {tache.titre} (propriétaire: {owner.nom})")
        return redirect(url_for('tasks.admin_liste'))

    except (ResourceNotFoundError, AuthorizationError) as e:
        log_and_flash(e.message, level="warning", flash_category="danger")
        return redirect(url_for('tasks.admin_liste'))

@tasks_bp.route('/changer-statut/<int:tache_id>/<string:nouveau_statut>')
@login_required
def changer_statut(tache_id: int, nouveau_statut: str):
    """Route for changing the status of a task."""
    try:
        tache = get_task_by_id(tache_id)
        verify_task_ownership(tache)

        # Validate the new status
        valid_statuses = ['pending', 'in_progress', 'completed']
        if nouveau_statut not in valid_statuses:
            log_and_flash("Statut invalide", level="warning", flash_category="danger")
            return redirect(url_for('tasks.liste'))

        tache.status = nouveau_statut
        tache.updated_at = datetime.utcnow()
        save_task(tache)
        log_and_flash(f"Statut de la tâche {tache.titre} changé à {nouveau_statut}")
        return redirect(url_for('tasks.liste'))

    except (ResourceNotFoundError, AuthorizationError) as e:
        log_and_flash(e.message, level="warning", flash_category="danger")
        return redirect(url_for('tasks.liste'))
