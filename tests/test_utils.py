"""
Unit tests for the Task Manager utility functions.
"""

import pytest
from flask import session, flash
from taskmanager.utils import (
    get_task_by_id, 
    verify_task_ownership, 
    log_and_flash, 
    populate_task_from_form, 
    save_task
)
from taskmanager.exceptions import ResourceNotFoundError, AuthorizationError
from taskmanager.models import Tache
from datetime import datetime

class TestGetTaskById:
    """Tests for the get_task_by_id function."""

    def test_get_existing_task(self, db_session, test_task):
        """Test getting an existing task by ID."""
        task = get_task_by_id(test_task.id)
        assert task is not None
        assert task.id == test_task.id
        assert task.titre == test_task.titre

    def test_get_nonexistent_task(self, db_session):
        """Test getting a nonexistent task by ID raises ResourceNotFoundError."""
        with pytest.raises(ResourceNotFoundError):
            get_task_by_id(999)  # Assuming ID 999 doesn't exist


class TestVerifyTaskOwnership:
    """Tests for the verify_task_ownership function."""

    def test_owner_can_access_task(self, app, test_user, test_task):
        """Test that the owner can access their task."""
        with app.test_request_context():
            # Set up session to simulate logged in user
            session['personne_id'] = test_user.id
            
            # This should not raise an exception
            verify_task_ownership(test_task)

    def test_non_owner_cannot_access_task(self, app, test_task):
        """Test that a non-owner cannot access someone else's task."""
        with app.test_request_context():
            # Set up session to simulate a different logged in user
            session['personne_id'] = test_task.personne_id + 1  # Different user ID
            
            with pytest.raises(AuthorizationError):
                verify_task_ownership(test_task)


class TestLogAndFlash:
    """Tests for the log_and_flash function."""

    def test_log_and_flash_info(self, app):
        """Test logging and flashing an info message."""
        with app.test_request_context():
            # Mock the flash function
            app.config['TESTING'] = True
            
            # Call the function
            log_and_flash("Test info message", "info", "success")
            
            # Since we're in a test context, we can't easily verify the flash message
            # In a real test, we might use a custom test client that captures flash messages


class TestPopulateTaskFromForm:
    """Tests for the populate_task_from_form function."""

    def test_populate_task(self, test_task):
        """Test populating a task from form data."""
        due_date = datetime.utcnow()
        form_data = {
            'titre': 'Updated Title',
            'description': 'Updated description',
            'status': 'completed',
            'priority': 'high',
            'due_date': due_date
        }
        
        updated_task = populate_task_from_form(test_task, form_data)
        
        assert updated_task.titre == 'Updated Title'
        assert updated_task.description == 'Updated description'
        assert updated_task.status == 'completed'
        assert updated_task.priority == 'high'
        assert updated_task.due_date == due_date


class TestSaveTask:
    """Tests for the save_task function."""

    def test_save_new_task(self, db_session, test_user, test_category):
        """Test saving a new task."""
        new_task = Tache(
            titre='New Task',
            description='A new task',
            status='pending',
            priority='medium',
            personne_id=test_user.id,
            categorie_id=test_category.id
        )
        
        save_task(new_task, is_new=True)
        
        # Verify the task was saved to the database
        saved_task = Tache.query.filter_by(titre='New Task').first()
        assert saved_task is not None
        assert saved_task.description == 'A new task'

    def test_update_existing_task(self, db_session, test_task):
        """Test updating an existing task."""
        test_task.titre = 'Updated Task'
        
        save_task(test_task, is_new=False)
        
        # Verify the task was updated in the database
        db_session.session.refresh(test_task)
        assert test_task.titre == 'Updated Task'