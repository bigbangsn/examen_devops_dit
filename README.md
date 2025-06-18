# Application de Gestion de Tâches

Une application complète de gestion de tâches construite avec Flask, permettant aux utilisateurs de créer, gérer et organiser des tâches avec des catégories, des priorités et des dates d'échéance.

## Fonctionnalités

- Authentification et autorisation des utilisateurs
- Gestion des profils utilisateurs avec photos, biographies et préférences
- Gestion des tâches avec statut, priorité et dates d'échéance
- Organisation des tâches par catégories avec filtrage
- Pagination des listes de tâches avec options de tri
- Design responsive avec interface Bootstrap
- Gestion complète des erreurs
- Journalisation et surveillance
- Optimisation des performances avec pooling de connexions à la base de données
- Requêtes optimisées pour une meilleure performance

## Stack Technologique

- **Backend**: Flask, SQLAlchemy
- **Base de données**: SQLite (développement), PostgreSQL (production)
- **Frontend**: HTML, CSS, JavaScript
- **Tests**: pytest, pytest-flask, pytest-cov
- **CI/CD**: GitHub Actions
- **Conteneurisation**: Docker, Docker Compose

## Installation

### Développement Local

1. Cloner le dépôt:
   ```
   git clone https://github.com/bigbangsn/taskmanager.git
   cd taskmanager
   ```

2. Créer et activer un environnement virtuel:
   ```
   python -m venv venv
   # Sur Windows
   venv\Scripts\activate
   # Sur macOS/Linux
   source venv/bin/activate
   ```

3. Installer les dépendances:
   ```
   pip install -r requirements.txt
   ```

4. Configurer la base de données:
   ```
   flask db upgrade
   ```

5. Lancer l'application:
   ```
   flask run
   ```

### Déploiement avec Docker

1. Cloner le dépôt:
   ```
   git clone https://github.com/bigbangsn/taskmanager.git
   cd taskmanager
   ```

2. Construire et démarrer les conteneurs:
   ```
   docker-compose up -d
   ```

3. Accéder à l'application sur http://localhost:5000

4. Pour arrêter les conteneurs:
   ```
   docker-compose down
   ```

## Tests

Exécuter les tests avec rapport de couverture:

```
python run_tests.py
```

Ou utiliser pytest directement:

```
pytest --cov=taskmanager
```

## Structure du Projet

- `app.py`: Point d'entrée de l'application
- `taskmanager/`: Package principal
  - `__init__.py`: Factory de l'application
  - `models.py`: Modèles de base de données
  - `utils.py`: Fonctions utilitaires
  - `auth/`: Blueprint d'authentification
  - `tasks/`: Blueprint des tâches
  - `categories/`: Blueprint des catégories
- `templates/`: Templates HTML
- `static/`: Fichiers statiques (CSS, JS)
- `tests/`: Suite de tests
- `migrations/`: Migrations de base de données
- `docs/`: Documentation du projet

## Contribution

1. Forker le dépôt
2. Créer une branche de fonctionnalité: `git checkout -b nom-fonctionnalite`
3. Committer vos changements: `git commit -m 'Ajouter une fonctionnalité'`
4. Pousser vers la branche: `git push origin nom-fonctionnalite`
5. Soumettre une pull request

## Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.
