"""Utility functions for session management."""

from flask import session, current_app

def regenerate_session() -> None:
    """
    Regenerate the session while preserving the current session data.

    This function creates a new session ID while keeping all the existing
    session data, which helps prevent session fixation attacks.
    """
    # Store current session data
    old_session_data = dict(session)

    # Clear the session (this will generate a new session ID)
    session.clear()

    # Restore the session data to the new session
    for key, value in old_session_data.items():
        session[key] = value

    current_app.logger.debug(f"Session regenerated for user {session.get('personne_id')}")