"""
Integration tests for the category routes.
"""

import pytest
from flask import url_for
from taskmanager.models import Categorie

class TestCategoryRoutes:
    """Tests for the category routes."""

    def test_category_list_page(self, auth_client):
        """Test that the category list page loads correctly."""
        response = auth_client.get('/categories/')
        assert response.status_code == 200
        assert b'Cat' in response.data  # Part of "Catégories" heading

    def test_category_list_shows_categories(self, auth_client, test_category):
        """Test that the category list shows existing categories."""
        response = auth_client.get('/categories/')
        assert response.status_code == 200
        assert test_category.nom.encode() in response.data

    def test_new_category_page(self, auth_client):
        """Test that the new category page loads correctly."""
        response = auth_client.get('/categories/nouvelle')
        assert response.status_code == 200
        assert b'Nouvelle Cat' in response.data  # Part of "Nouvelle Catégorie" heading

    def test_create_category(self, auth_client, db_session):
        """Test creating a new category."""
        response = auth_client.post('/categories/nouvelle', data={
            'nom': 'New Test Category',
            'description': 'This is a test category',
            'couleur': '#00FF00'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'New Test Category' in response.data
        
        # Check that the category was created in the database
        category = Categorie.query.filter_by(nom='New Test Category').first()
        assert category is not None
        assert category.description == 'This is a test category'
        assert category.couleur == '#00FF00'

    def test_edit_category_page(self, auth_client, test_category):
        """Test that the edit category page loads correctly."""
        response = auth_client.get(f'/categories/editer/{test_category.id}')
        assert response.status_code == 200
        assert b'diter la Cat' in response.data  # Part of "Éditer la Catégorie" heading
        assert test_category.nom.encode() in response.data

    def test_edit_category(self, auth_client, db_session, test_category):
        """Test editing an existing category."""
        response = auth_client.post(f'/categories/editer/{test_category.id}', data={
            'nom': 'Updated Category Name',
            'description': 'Updated category description',
            'couleur': '#FF0000'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Updated Category Name' in response.data
        
        # Check that the category was updated in the database
        db_session.session.refresh(test_category)
        assert test_category.nom == 'Updated Category Name'
        assert test_category.description == 'Updated category description'
        assert test_category.couleur == '#FF0000'

    def test_delete_category(self, auth_client, db_session, test_category):
        """Test deleting a category."""
        # First, make sure there are no tasks in this category
        # This might require modifying the test_task fixture or creating a new category
        response = auth_client.get(f'/categories/supprimer/{test_category.id}', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'supprim' in response.data  # Part of success message
        
        # Check that the category was deleted from the database
        category = Categorie.query.get(test_category.id)
        assert category is None
        
        # Check that the category doesn't appear in the category list
        response = auth_client.get('/categories/')
        assert test_category.nom.encode() not in response.data

    def test_delete_category_with_tasks(self, auth_client, db_session, test_category, test_task):
        """Test attempting to delete a category that has tasks."""
        response = auth_client.get(f'/categories/supprimer/{test_category.id}', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'impossible de supprimer' in response.data  # Part of error message
        
        # Check that the category still exists in the database
        category = Categorie.query.get(test_category.id)
        assert category is not None

    def test_access_nonexistent_category(self, auth_client):
        """Test accessing a nonexistent category."""
        response = auth_client.get('/categories/editer/999', follow_redirects=True)
        
        assert response.status_code == 404
        assert b'introuvable' in response.data  # Part of error message

    def test_access_category_without_authentication(self, client, test_category):
        """Test accessing a category without being authenticated."""
        response = client.get(f'/categories/editer/{test_category.id}', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Connexion' in response.data  # Redirected to login page