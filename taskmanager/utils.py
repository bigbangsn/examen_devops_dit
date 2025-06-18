"""Utility functions for the Task Manager application."""

from flask import session, flash, current_app, redirect, url_for
from typing import Optional, Tuple, Any, Dict, Union, List
from sqlalchemy import func, desc, asc
from sqlalchemy.orm import joinedload, contains_eager
from taskmanager import db
from taskmanager.models import Tache, Categorie, Personne
from taskmanager.exceptions import AuthorizationError, ResourceNotFoundError
from markupsafe import escape

def get_task_by_id(task_id: int) -> Tache:
    """
    Get a task by ID or raise a ResourceNotFoundError if it doesn't exist.

    Args:
        task_id: The ID of the task to retrieve

    Returns:
        The task object

    Raises:
        ResourceNotFoundError: If the task doesn't exist
    """
    task = Tache.query.get(task_id)
    if not task:
        raise ResourceNotFoundError("Tâche", task_id)
    return task

def verify_task_ownership(task: Tache) -> None:
    """
    Verify that the current user owns the task.

    Args:
        task: The task to check

    Raises:
        AuthorizationError: If the current user doesn't own the task
    """
    if task.personne_id != session.get('personne_id'):
        current_app.logger.warning(
            f"Tentative d'accès non autorisé à la tâche {task.id} par l'utilisateur {session.get('personne_id')}"
        )
        raise AuthorizationError("Vous n'êtes pas autorisé à accéder à cette tâche")

def log_and_flash(message: str, level: str = "info", flash_category: str = "success") -> None:
    """
    Log a message and flash it to the user.

    Args:
        message: The message to log and flash
        level: The log level (debug, info, warning, error)
        flash_category: The flash message category (success, info, warning, danger)
    """
    if level == "debug":
        current_app.logger.debug(message)
    elif level == "info":
        current_app.logger.info(message)
    elif level == "warning":
        current_app.logger.warning(message)
    elif level == "error":
        current_app.logger.error(message)

    flash(message, flash_category)

def populate_task_from_form(task: Tache, form_data: Dict[str, Any]) -> Tache:
    """
    Populate a task object from form data.

    Args:
        task: The task object to populate
        form_data: The form data to use

    Returns:
        The populated task object
    """
    # Sanitize text inputs
    titre = form_data.get('titre')
    if titre:
        task.titre = escape(titre.strip())

    description = form_data.get('description')
    if description:
        task.description = escape(description.strip())
    else:
        task.description = None

    # Non-text inputs don't need sanitization
    task.status = form_data.get('status')
    task.priority = form_data.get('priority')
    task.due_date = form_data.get('due_date')

    # Handle category assignment
    categorie_id = form_data.get('categorie_id')
    if categorie_id is not None:
        # If categorie_id is 0, it means "No category"
        if categorie_id == 0:
            task.categorie_id = None
        else:
            task.categorie_id = categorie_id

    return task

def save_task(task: Tache, is_new: bool = False) -> None:
    """
    Save a task to the database.

    Args:
        task: The task to save
        is_new: Whether the task is new (True) or existing (False)
    """
    if is_new:
        db.session.add(task)
    db.session.commit()

# Query optimization functions

def get_admin_tasks_optimized(
    page: int = 1, 
    per_page: int = 10, 
    status: Optional[str] = None,
    priority: Optional[str] = None,
    user_id: Optional[int] = None,
    category_id: Optional[int] = None,
    search_term: Optional[str] = None,
    sort_by: str = 'due_date',
    sort_dir: str = 'asc'
) -> Tuple[List[Tache], int, int]:
    """
    Get all tasks with optimized queries, filtering, sorting, and pagination for admin view.

    Args:
        page: The page number (1-indexed)
        per_page: The number of items per page
        status: Filter by status (pending, in_progress, completed)
        priority: Filter by priority (low, medium, high)
        user_id: Filter by user ID
        category_id: Filter by category ID
        search_term: Search term for task title or description
        sort_by: Field to sort by (due_date, created_at, priority, status, titre)
        sort_dir: Sort direction (asc or desc)

    Returns:
        Tuple containing:
        - List of tasks for the current page
        - Total number of tasks matching the filters
        - Total number of pages
    """
    # Start with a query that eagerly loads the category and user to avoid N+1 queries
    query = Tache.query.options(
        joinedload(Tache.categorie),
        joinedload(Tache.personne)
    ).filter(
        Tache.is_deleted == False
    )

    # Apply filters
    if status:
        query = query.filter(Tache.status == status)

    if priority:
        query = query.filter(Tache.priority == priority)

    if user_id:
        query = query.filter(Tache.personne_id == user_id)

    if category_id:
        query = query.filter(Tache.categorie_id == category_id)

    if search_term:
        search_pattern = f"%{search_term}%"
        query = query.filter(
            db.or_(
                Tache.titre.ilike(search_pattern),
                Tache.description.ilike(search_pattern)
            )
        )

    # Apply sorting
    if sort_by == 'due_date':
        # Handle NULL due_dates by sorting them last
        if sort_dir == 'asc':
            query = query.order_by(
                Tache.due_date.is_(None).asc(),
                Tache.due_date.asc()
            )
        else:
            query = query.order_by(
                Tache.due_date.is_(None).desc(),
                Tache.due_date.desc()
            )
    elif sort_by == 'created_at':
        query = query.order_by(
            desc(Tache.created_at) if sort_dir == 'desc' else asc(Tache.created_at)
        )
    elif sort_by == 'priority':
        # Custom priority ordering (high, medium, low)
        priority_order = case(
            {'high': 1, 'medium': 2, 'low': 3},
            value=Tache.priority
        )
        query = query.order_by(
            desc(priority_order) if sort_dir == 'desc' else asc(priority_order)
        )
    elif sort_by == 'status':
        # Custom status ordering (pending, in_progress, completed)
        status_order = case(
            {'pending': 1, 'in_progress': 2, 'completed': 3},
            value=Tache.status
        )
        query = query.order_by(
            desc(status_order) if sort_dir == 'desc' else asc(status_order)
        )
    elif sort_by == 'user':
        # Sort by user name
        query = query.join(Personne).order_by(
            desc(Personne.nom) if sort_dir == 'desc' else asc(Personne.nom)
        )
    else:  # Default to title
        query = query.order_by(
            desc(Tache.titre) if sort_dir == 'desc' else asc(Tache.titre)
        )

    # Get total count for pagination
    total_count = query.count()
    total_pages = (total_count + per_page - 1) // per_page  # Ceiling division

    # Apply pagination
    tasks = query.limit(per_page).offset((page - 1) * per_page).all()

    return tasks, total_count, total_pages

def get_tasks_optimized(
    user_id: int, 
    page: int = 1, 
    per_page: int = 10, 
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category_id: Optional[int] = None,
    search_term: Optional[str] = None,
    sort_by: str = 'due_date',
    sort_dir: str = 'asc'
) -> Tuple[List[Tache], int, int]:
    """
    Get tasks for a user with optimized queries, filtering, sorting, and pagination.

    Args:
        user_id: The ID of the user whose tasks to retrieve
        page: The page number (1-indexed)
        per_page: The number of items per page
        status: Filter by status (pending, in_progress, completed)
        priority: Filter by priority (low, medium, high)
        category_id: Filter by category ID
        search_term: Search term for task title or description
        sort_by: Field to sort by (due_date, created_at, priority, status, titre)
        sort_dir: Sort direction (asc or desc)

    Returns:
        Tuple containing:
        - List of tasks for the current page
        - Total number of tasks matching the filters
        - Total number of pages
    """
    # Start with a query that eagerly loads the category to avoid N+1 queries
    query = Tache.query.options(
        joinedload(Tache.categorie)
    ).filter(
        Tache.personne_id == user_id,
        Tache.is_deleted == False
    )

    # Apply filters
    if status:
        query = query.filter(Tache.status == status)

    if priority:
        query = query.filter(Tache.priority == priority)

    if category_id:
        query = query.filter(Tache.categorie_id == category_id)

    if search_term:
        search_pattern = f"%{search_term}%"
        query = query.filter(
            db.or_(
                Tache.titre.ilike(search_pattern),
                Tache.description.ilike(search_pattern)
            )
        )

    # Apply sorting
    if sort_by == 'due_date':
        # Handle NULL due_dates by sorting them last
        if sort_dir == 'asc':
            query = query.order_by(
                Tache.due_date.is_(None).asc(),
                Tache.due_date.asc()
            )
        else:
            query = query.order_by(
                Tache.due_date.is_(None).desc(),
                Tache.due_date.desc()
            )
    elif sort_by == 'created_at':
        query = query.order_by(
            desc(Tache.created_at) if sort_dir == 'desc' else asc(Tache.created_at)
        )
    elif sort_by == 'priority':
        # Custom priority ordering (high, medium, low)
        priority_order = case(
            {'high': 1, 'medium': 2, 'low': 3},
            value=Tache.priority
        )
        query = query.order_by(
            desc(priority_order) if sort_dir == 'desc' else asc(priority_order)
        )
    elif sort_by == 'status':
        # Custom status ordering (pending, in_progress, completed)
        status_order = case(
            {'pending': 1, 'in_progress': 2, 'completed': 3},
            value=Tache.status
        )
        query = query.order_by(
            desc(status_order) if sort_dir == 'desc' else asc(status_order)
        )
    else:  # Default to title
        query = query.order_by(
            desc(Tache.titre) if sort_dir == 'desc' else asc(Tache.titre)
        )

    # Get total count for pagination
    total_count = query.count()
    total_pages = (total_count + per_page - 1) // per_page  # Ceiling division

    # Apply pagination
    tasks = query.limit(per_page).offset((page - 1) * per_page).all()

    return tasks, total_count, total_pages

def get_categories_optimized(user_id: int) -> List[Categorie]:
    """
    Get categories for a user with optimized queries.

    Args:
        user_id: The ID of the user whose categories to retrieve

    Returns:
        List of categories
    """
    # Query categories with a count of active tasks in each category
    return db.session.query(
        Categorie,
        func.count(Tache.id).label('task_count')
    ).outerjoin(
        Tache, db.and_(
            Tache.categorie_id == Categorie.id,
            Tache.is_deleted == False
        )
    ).filter(
        Categorie.personne_id == user_id
    ).group_by(
        Categorie.id
    ).order_by(
        Categorie.nom
    ).all()

def get_task_stats(user_id: int) -> Dict[str, int]:
    """
    Get task statistics for a user.

    Args:
        user_id: The ID of the user

    Returns:
        Dictionary with task statistics
    """
    # Query for task counts by status
    status_counts = db.session.query(
        Tache.status,
        func.count(Tache.id)
    ).filter(
        Tache.personne_id == user_id,
        Tache.is_deleted == False
    ).group_by(
        Tache.status
    ).all()

    # Convert to dictionary
    stats = {
        'total': 0,
        'pending': 0,
        'in_progress': 0,
        'completed': 0
    }

    for status, count in status_counts:
        stats[status] = count
        stats['total'] += count

    # Add overdue tasks count
    overdue_count = db.session.query(
        func.count(Tache.id)
    ).filter(
        Tache.personne_id == user_id,
        Tache.is_deleted == False,
        Tache.status != 'completed',
        Tache.due_date < func.current_date(),
        Tache.due_date.isnot(None)
    ).scalar()

    stats['overdue'] = overdue_count or 0

    return stats

# Helper function for case statements
def case(mapping, value):
    """
    Create a CASE statement for custom ordering.

    Args:
        mapping: Dictionary mapping values to sort order
        value: The column to check

    Returns:
        A case expression for ordering
    """
    whens = []
    for val, order in mapping.items():
        whens.append((value == val, order))

    return func.case(*whens, else_=len(mapping) + 1)
