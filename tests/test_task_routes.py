"""
Integration tests for the task routes.
"""

import pytest
from flask import url_for
from taskmanager.models import Tache
from datetime import datetime, timedelta

class TestTaskRoutes:
    """Tests for the task routes."""

    def test_task_list_page(self, auth_client):
        """Test that the task list page loads correctly."""
        response = auth_client.get('/tasks/')
        assert response.status_code == 200
        assert b'Mes T' in response.data  # Part of "Mes Tâches" heading

    def test_task_list_shows_tasks(self, auth_client, test_task):
        """Test that the task list shows existing tasks."""
        response = auth_client.get('/tasks/')
        assert response.status_code == 200
        assert test_task.titre.encode() in response.data

    def test_new_task_page(self, auth_client):
        """Test that the new task page loads correctly."""
        response = auth_client.get('/tasks/nouvelle')
        assert response.status_code == 200
        assert b'Nouvelle T' in response.data  # Part of "Nouvelle Tâche" heading

    def test_create_task(self, auth_client, db_session, test_category):
        """Test creating a new task."""
        due_date = (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d')
        response = auth_client.post('/tasks/nouvelle', data={
            'titre': 'New Test Task',
            'description': 'This is a test task',
            'status': 'pending',
            'priority': 'medium',
            'due_date': due_date,
            'categorie_id': test_category.id
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'New Test Task' in response.data
        
        # Check that the task was created in the database
        task = Tache.query.filter_by(titre='New Test Task').first()
        assert task is not None
        assert task.description == 'This is a test task'
        assert task.status == 'pending'
        assert task.priority == 'medium'
        assert task.categorie_id == test_category.id

    def test_edit_task_page(self, auth_client, test_task):
        """Test that the edit task page loads correctly."""
        response = auth_client.get(f'/tasks/editer/{test_task.id}')
        assert response.status_code == 200
        assert b'diter la T' in response.data  # Part of "Éditer la Tâche" heading
        assert test_task.titre.encode() in response.data

    def test_edit_task(self, auth_client, db_session, test_task):
        """Test editing an existing task."""
        response = auth_client.post(f'/tasks/editer/{test_task.id}', data={
            'titre': 'Updated Task Title',
            'description': 'Updated task description',
            'status': 'in_progress',
            'priority': 'high',
            'due_date': '',
            'categorie_id': test_task.categorie_id
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Updated Task Title' in response.data
        
        # Check that the task was updated in the database
        db_session.session.refresh(test_task)
        assert test_task.titre == 'Updated Task Title'
        assert test_task.description == 'Updated task description'
        assert test_task.status == 'in_progress'
        assert test_task.priority == 'high'

    def test_delete_task(self, auth_client, db_session, test_task):
        """Test deleting a task."""
        response = auth_client.get(f'/tasks/supprimer/{test_task.id}', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'supprim' in response.data  # Part of success message
        
        # Check that the task was soft deleted
        db_session.session.refresh(test_task)
        assert test_task.is_deleted is True
        
        # Check that the task doesn't appear in the task list
        response = auth_client.get('/tasks/')
        assert test_task.titre.encode() not in response.data

    def test_change_task_status(self, auth_client, db_session, test_task):
        """Test changing a task's status."""
        response = auth_client.get(f'/tasks/changer-statut/{test_task.id}/completed', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'statut a' in response.data  # Part of success message
        
        # Check that the task status was updated
        db_session.session.refresh(test_task)
        assert test_task.status == 'completed'

    def test_access_nonexistent_task(self, auth_client):
        """Test accessing a nonexistent task."""
        response = auth_client.get('/tasks/editer/999', follow_redirects=True)
        
        assert response.status_code == 404
        assert b'introuvable' in response.data  # Part of error message

    def test_access_task_without_authentication(self, client, test_task):
        """Test accessing a task without being authenticated."""
        response = client.get(f'/tasks/editer/{test_task.id}', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Connexion' in response.data  # Redirected to login page