from flask import render_template, redirect, url_for, flash, request, current_app, session
from werkzeug.security import check_password_hash, generate_password_hash
from taskmanager import db
from taskmanager.models import Personne
from taskmanager.users import users_bp
from taskmanager.auth.routes import login_required
from taskmanager.utils import log_and_flash
from taskmanager.profile_form import ProfileForm
from datetime import datetime
from markupsafe import escape
import os
from werkzeug.utils import secure_filename

@users_bp.route('/profile')
@login_required
def profile():
    """Route for viewing user's own profile."""
    user_id = session.get('personne_id')
    if not user_id:
        flash("Vous devez être connecté pour accéder à cette page.", "danger")
        return redirect(url_for('auth.connexion'))
    
    user = Personne.query.get_or_404(user_id)
    return render_template('users/profile.html', user=user)

@users_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Route for editing user's own profile."""
    user_id = session.get('personne_id')
    if not user_id:
        flash("Vous devez être connecté pour accéder à cette page.", "danger")
        return redirect(url_for('auth.connexion'))
    
    user = Personne.query.get_or_404(user_id)
    form = ProfileForm(user_id=user_id)
    
    # Pre-populate form with existing data
    if request.method == 'GET':
        form.email.data = user.email
        form.bio.data = user.bio
        form.notification_preferences.data = user.notification_preferences
    
    if form.validate_on_submit():
        try:
            # Update email and bio if provided
            if form.email.data:
                user.email = escape(form.email.data.strip())
            if form.bio.data:
                user.bio = escape(form.bio.data.strip())
            
            # Update notification preferences
            user.notification_preferences = form.notification_preferences.data
            
            # Handle password change if provided
            if form.current_password.data and form.new_password.data:
                if check_password_hash(user.password, form.current_password.data):
                    user.password = generate_password_hash(form.new_password.data)
                else:
                    flash("Mot de passe actuel incorrect.", "danger")
                    return render_template('users/edit_profile.html', form=form)
            
            # Handle profile picture upload if provided
            if form.profile_picture.data:
                filename = secure_filename(form.profile_picture.data.filename)
                if filename:
                    # Create uploads directory if it doesn't exist
                    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'profile_pics')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Save the file
                    file_path = os.path.join(upload_folder, f"user_{user_id}_{filename}")
                    form.profile_picture.data.save(file_path)
                    
                    # Update user's profile picture path
                    user.profile_picture = f"uploads/profile_pics/user_{user_id}_{filename}"
            
            # Update timestamp and save changes
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_and_flash("Profil mis à jour avec succès!", level="info")
            return redirect(url_for('users.profile'))
            
        except Exception as e:
            db.session.rollback()
            log_and_flash(f"Erreur lors de la mise à jour du profil: {str(e)}", level="error", flash_category="danger")
    
    return render_template('users/edit_profile.html', form=form)