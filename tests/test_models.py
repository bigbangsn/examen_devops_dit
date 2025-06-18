"""
Unit tests for the Task Manager models.
"""

import pytest
from datetime import datetime, timedelta
from taskmanager.models import Personne, Categorie, Tache

class TestPersonneModel:
    """Tests for the Personne model."""

    def test_create_personne(self, db_session):
        """Test creating a new user."""
        user = Personne(
            nom='testuser',
            password='hashed_password'
        )
        db_session.session.add(user)
        db_session.session.commit()

        saved_user = Personne.query.filter_by(nom='testuser').first()
        assert saved_user is not None
        assert saved_user.nom == 'testuser'
        assert saved_user.password == 'hashed_password'
        assert saved_user.created_at is not None
        assert saved_user.updated_at is not None

    def test_personne_relationship(self, test_user, test_task):
        """Test the relationship between Personne and Tache."""
        assert len(test_user.taches) == 1
        assert test_user.taches[0].titre == 'Test Task'

    def test_personne_repr(self, test_user):
        """Test the string representation of a Personne."""
        assert repr(test_user) == f"<Personne {test_user.nom}>"


class TestCategorieModel:
    """Tests for the Categorie model."""

    def test_create_categorie(self, db_session, test_user):
        """Test creating a new category."""
        category = Categorie(
            nom='Work',
            description='Work-related tasks',
            couleur='#FF5733',
            personne_id=test_user.id
        )
        db_session.session.add(category)
        db_session.session.commit()

        saved_category = Categorie.query.filter_by(nom='Work').first()
        assert saved_category is not None
        assert saved_category.nom == 'Work'
        assert saved_category.description == 'Work-related tasks'
        assert saved_category.couleur == '#FF5733'
        assert saved_category.personne_id == test_user.id
        assert saved_category.created_at is not None
        assert saved_category.updated_at is not None

    def test_categorie_relationship(self, test_category, test_task):
        """Test the relationship between Categorie and Tache."""
        assert len(test_category.taches) == 1
        assert test_category.taches[0].titre == 'Test Task'

    def test_categorie_repr(self, test_category):
        """Test the string representation of a Categorie."""
        assert repr(test_category) == f"<Categorie {test_category.nom}>"


class TestTacheModel:
    """Tests for the Tache model."""

    def test_create_tache(self, db_session, test_user, test_category):
        """Test creating a new task."""
        due_date = datetime.utcnow() + timedelta(days=7)
        task = Tache(
            titre='New Task',
            description='A new task description',
            status='in_progress',
            priority='high',
            due_date=due_date,
            personne_id=test_user.id,
            categorie_id=test_category.id
        )
        db_session.session.add(task)
        db_session.session.commit()

        saved_task = Tache.query.filter_by(titre='New Task').first()
        assert saved_task is not None
        assert saved_task.titre == 'New Task'
        assert saved_task.description == 'A new task description'
        assert saved_task.status == 'in_progress'
        assert saved_task.priority == 'high'
        assert saved_task.due_date == due_date
        assert saved_task.personne_id == test_user.id
        assert saved_task.categorie_id == test_category.id
        assert saved_task.created_at is not None
        assert saved_task.updated_at is not None
        assert saved_task.is_deleted is False

    def test_tache_repr(self, test_task):
        """Test the string representation of a Tache."""
        assert repr(test_task) == f"<Tache {test_task.titre}>"

    def test_get_active_tasks(self, db_session, test_user, test_task):
        """Test getting active tasks for a user."""
        # Create a deleted task
        deleted_task = Tache(
            titre='Deleted Task',
            description='A deleted task',
            status='pending',
            priority='low',
            personne_id=test_user.id,
            is_deleted=True
        )
        db_session.session.add(deleted_task)
        db_session.session.commit()

        active_tasks = Tache.get_active_tasks(test_user.id)
        assert len(active_tasks) == 1
        assert active_tasks[0].titre == 'Test Task'
        assert active_tasks[0].is_deleted is False

    def test_soft_delete(self, db_session, test_task):
        """Test soft deleting a task."""
        test_task.soft_delete()
        
        # Refresh the task from the database
        db_session.session.refresh(test_task)
        
        assert test_task.is_deleted is True
        
        # Verify the task is not returned by get_active_tasks
        active_tasks = Tache.get_active_tasks(test_task.personne_id)
        assert len(active_tasks) == 0