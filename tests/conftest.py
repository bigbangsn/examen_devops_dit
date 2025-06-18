"""
Pytest configuration file for the Task Manager application.

This file contains fixtures and configuration for testing the application.
"""

import os
import pytest
from taskmanager import create_app, db
from taskmanager.models import Personne, Categorie, Tache
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

@pytest.fixture(scope='function')
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary file for the test database
    db_path = os.path.join(os.path.dirname(__file__), 'test_database.db')

    # Create the app with the test configuration
    app = create_app('testing')
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
    })

    # Create the database and the database tables
    with app.app_context():
        db.create_all()

    yield app

    # Remove the temporary database
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='function')
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def db_session(app):
    """Create a fresh database session for a test."""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def test_user(db_session):
    """Create a test user."""
    user = Personne(
        nom='testuser',
        password=generate_password_hash('password123')
    )
    db_session.session.add(user)
    db_session.session.commit()
    return user

@pytest.fixture(scope='function')
def test_category(db_session, test_user):
    """Create a test category."""
    category = Categorie(
        nom='Test Category',
        description='A test category',
        couleur='#FF5733',
        personne_id=test_user.id
    )
    db_session.session.add(category)
    db_session.session.commit()
    return category

@pytest.fixture(scope='function')
def test_task(db_session, test_user, test_category):
    """Create a test task."""
    task = Tache(
        titre='Test Task',
        description='A test task',
        status='pending',
        priority='medium',
        due_date=datetime.utcnow() + timedelta(days=7),
        personne_id=test_user.id,
        categorie_id=test_category.id
    )
    db_session.session.add(task)
    db_session.session.commit()
    return task

@pytest.fixture(scope='function')
def auth_client(client, test_user):
    """A test client with authentication."""
    client.post('/auth/connexion', data={
        'nom': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    return client
