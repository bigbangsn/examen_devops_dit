from flask import Flask, render_template, redirect, url_for, session, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from forms import EnregistreForm, ConnexionForm, TacheForm
from models import db , Personne, Tache
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecret'



db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def accueil():
    if 'personne_id' in session:
        return redirect(url_for('taches'))
    return redirect(url_for('connexion'))

@app.route('/enregistrer', methods=['GET', 'POST'])
def enregistrer():
    form = EnregistreForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        personne = Personne(nom=form.nom.data, password=hashed_pw)
        db.session.add(personne)
        db.session.commit()
        flash("Compte créé ! Connectez-vous.", "success")
        return redirect(url_for('connexion'))
    return render_template('enregistrer.html', form=form)

@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    form = ConnexionForm()
    if form.validate_on_submit():
        personne = Personne.query.filter_by(nom=form.nom.data).first()
        if personne and check_password_hash(personne.password, form.password.data):
            session['personne_id'] = personne.id
            return redirect(url_for('taches'))
        flash("Identifiants invalides.", "danger")
    return render_template('connexion.html', form=form)

@app.route('/deconnecter')
def deconnecter():
    session.pop('personne_id', None)
    return redirect(url_for('connexion'))

@app.route('/taches')
def taches():
    if 'personne_id' not in session:
        return redirect(url_for('connexion'))
    personne_taches = Tache.query.filter_by(personne_id=session['personne_id']).all()
    return render_template('taches.html', taches=personne_taches)

@app.route('/tache/nouvelle', methods=['GET', 'POST'])
@app.route('/tache/editer/<int:tache_id>', methods=['GET', 'POST'])
def tache_form(tache_id=None):
    if 'personne_id' not in session:
        return redirect(url_for('connexion'))

    form = TacheForm()
    tache= Tache.query.get(tache_id) if tache_id else None

    if tache_id and tache.personne_id != session['personne_id']:
        flash("Accès non autorisé", "danger")
        return redirect(url_for('taches'))

    if form.validate_on_submit():
        if tache:
            tache.titre = form.titre.data
        else:
            tache = Tache(titre=form.titre.data, personne_id=session['personne_id'])
            db.session.add(tache)
        db.session.commit()
        return redirect(url_for('taches'))

    if request.method == 'GET' and tache:
        form.titre.data = tache.titre

    return render_template('ajouter_editer_tache.html', form=form)

@app.route('/tache/supprimer/<int:tache_id>')
def supprimer_tache(tache_id):
    tache = Tache.query.get(tache_id)
    if tache and tache.personne_id == session['personne_id']:
        db.session.delete(tache)
        db.session.commit()
    return redirect(url_for('taches'))

if __name__ == '__main__':
    app.run(debug=True)