from flask import Blueprint

users_bp = Blueprint('users', __name__, url_prefix='/users')

from taskmanager.users import routes
from taskmanager.users import profile_routes
