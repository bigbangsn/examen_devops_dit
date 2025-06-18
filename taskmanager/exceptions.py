"""Custom exceptions for the Task Manager application."""

from typing import Optional


class TaskManagerException(Exception):
    """Base exception for all Task Manager exceptions."""

    def __init__(self, message: str = "An error occurred in the Task Manager application"):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(TaskManagerException):
    """Exception raised for authentication errors."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class AuthorizationError(TaskManagerException):
    """Exception raised for authorization errors."""

    def __init__(self, message: str = "You are not authorized to perform this action"):
        super().__init__(message)


class ResourceNotFoundError(TaskManagerException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: Optional[int] = None):
        message = f"{resource_type} not found"
        if resource_id is not None:
            message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message)


class ValidationError(TaskManagerException):
    """Exception raised for data validation errors."""

    def __init__(self, message: str = "Invalid data provided"):
        super().__init__(message)


class DatabaseError(TaskManagerException):
    """Exception raised for database-related errors."""

    def __init__(self, message: str = "A database error occurred"):
        super().__init__(message)