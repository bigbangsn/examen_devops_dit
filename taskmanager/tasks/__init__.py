from flask import Blueprint

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

from taskmanager.tasks import routes