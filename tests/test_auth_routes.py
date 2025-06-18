"""
Integration tests for the authentication routes.
"""

import pytest
from flask import session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from taskmanager.models import Personne

class TestAuthRoutes:
    """Tests for the authentication routes."""

    def test_register_page(self, client):
        """Test that the register page loads correctly."""
        response = client.get('/auth/enregistrer')
        assert response.status_code == 200
        assert b'Enregistrer un nouveau compte' in response.data

    def test_register_user(self, client, db_session):
        """Test registering a new user."""
        response = client.post('/auth/enregistrer', data={
            'nom': 'newuser',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Compte cr' in response.data  # Part of success message
        
        # Check that the user was created in the database
        user = Personne.query.filter_by(nom='newuser').first()
        assert user is not None
        assert check_password_hash(user.password, 'password123')

    def test_register_duplicate_user(self, client, test_user):
        """Test registering a user with a name that already exists."""
        response = client.post('/auth/enregistrer', data={
            'nom': 'testuser',  # Same as test_user
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Ce nom d\'utilisateur est d' in response.data  # Error message

    def test_login_page(self, client):
        """Test that the login page loads correctly."""
        response = client.get('/auth/connexion')
        assert response.status_code == 200
        assert b'Connexion' in response.data

    def test_login_valid_user(self, client, test_user):
        """Test logging in with valid credentials."""
        # Update the test user's password to a known hash
        with client.application.app_context():
            test_user.password = generate_password_hash('password123')
            client.application.extensions['sqlalchemy'].db.session.commit()
        
        response = client.post('/auth/connexion', data={
            'nom': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Connexion r' in response.data  # Part of success message
        
        # Check that the user is logged in
        with client.session_transaction() as sess:
            assert 'personne_id' in sess
            assert sess['personne_id'] == test_user.id

    def test_login_invalid_user(self, client):
        """Test logging in with invalid credentials."""
        response = client.post('/auth/connexion', data={
            'nom': 'nonexistentuser',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Nom d\'utilisateur ou mot de passe incorrect' in response.data

    def test_login_invalid_password(self, client, test_user):
        """Test logging in with an invalid password."""
        response = client.post('/auth/connexion', data={
            'nom': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Nom d\'utilisateur ou mot de passe incorrect' in response.data

    def test_logout(self, auth_client):
        """Test logging out."""
        response = auth_client.get('/auth/deconnecter', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Vous avez' in response.data  # Part of logout message
        
        # Check that the user is logged out
        with auth_client.session_transaction() as sess:
            assert 'personne_id' not in sess