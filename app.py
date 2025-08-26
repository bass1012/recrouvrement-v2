from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from wtforms import StringField, TextAreaField, DateField, SubmitField, SelectField, FileField, PasswordField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from io import BytesIO
import base64
from sqlalchemy import or_

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'votre-cle-secrete-ici-changez-moi')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///clients.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ajouter le filtre nl2br pour Jinja2
@app.template_filter('nl2br')
def nl2br_filter(text):
    return text.replace('\n', '<br>\n') if text else ''

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'

# Modèle de base de données pour les clients
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telephone = db.Column(db.String(20))
    date_derniere_visite = db.Column(db.Date)
    date_ajout = db.Column(db.Date, default=lambda: datetime.now().date())
    date_expiration = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    statut = db.Column(db.String(20), default='actif')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    sujet = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    sujet = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(20), default='envoyé')
    client = db.relationship('Client', backref=db.backref('emails', lazy=True))

    def __repr__(self):
        return f'<Client {self.nom}>'

# Modèle de base de données pour les utilisateurs
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Formulaire pour ajouter/modifier un client
class ClientForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telephone = StringField('Téléphone')
    date_derniere_visite = DateField('Date dernière visite')
    date_expiration = DateField('Date d\'expiration', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    statut = SelectField('Statut', choices=[('actif', 'Actif'), ('inactif', 'Inactif')])
    submit = SubmitField('Enregistrer')

# Formulaire pour envoyer un email
class EmailForm(FlaskForm):
    sujet = StringField('Sujet', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Envoyer')

# Formulaire pour uploader une signature
class SignatureForm(FlaskForm):
    signature = FileField('Image de signature')
    submit = SubmitField('Télécharger')

# Formulaire de connexion
class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

# Formulaire d'inscription
class RegisterForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('S\'inscrire')

def envoyer_email(destinataire_email, destinataire_nom, sujet, message):
    """Fonction pour envoyer un email avec signature image"""
    try:
        # Configuration SMTP (à adapter selon votre fournisseur)
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        email_expediteur = os.getenv('EMAIL_EXPEDITEUR')
        mot_de_passe = os.getenv('MOT_DE_PASSE_EMAIL')
        
        if not email_expediteur or not mot_de_passe:
            return False, "Configuration email manquante"
        
        # Création du message multipart
        msg = MIMEMultipart('related')
        msg['From'] = email_expediteur
        msg['To'] = destinataire_email
        msg['Subject'] = sujet
        
        # Création du conteneur pour le texte et HTML
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        
        # Corps du message en HTML avec signature image
        corps_html = f"""
        <html>
        <body>
            <p>Bonjour {destinataire_nom},</p>
            <br>
            <p>{message.replace(chr(10), '<br>')}</p>
            <br>
            <p>Cordialement,<br>
            Votre équipe</p>
            <br>
            <img src="cid:signature" style="max-width: 300px; height: auto;">
        </body>
        </html>
        """
        
        # Version texte pour compatibilité
        corps_texte = f"""
        Bonjour {destinataire_nom},
        
        {message}
        
        Cordialement,
        """
        
        # Attacher les versions texte et HTML
        msg_alternative.attach(MIMEText(corps_texte, 'plain', 'utf-8'))
        msg_alternative.attach(MIMEText(corps_html, 'html', 'utf-8'))
        
        # Attacher l'image de signature si elle existe
        signature_path = os.path.join('static', 'images', 'signature.png')
        if os.path.exists(signature_path) and os.path.getsize(signature_path) > 0:
            with open(signature_path, 'rb') as f:
                img_data = f.read()
                image = MIMEImage(img_data)
                image.add_header('Content-ID', '<signature>')
                image.add_header('Content-Disposition', 'inline', filename='signature.png')
                msg.attach(image)
        
        # Envoi de l'email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_expediteur, mot_de_passe)
        text = msg.as_string()
        server.sendmail(email_expediteur, destinataire_email, text)
        server.quit()
        
        return True, "Email envoyé avec succès"
        
    except Exception as e:
        return False, f"Erreur lors de l'envoi: {str(e)}"

def envoyer_rappels_automatiques():
    """Fonction pour envoyer des rappels automatiques aux clients avant expiration"""
    with app.app_context():
        # Clients dont l'expiration arrive dans 2 jours
        date_alerte = datetime.now().date() + timedelta(days=2)
        clients_a_alerter = Client.query.filter(
            Client.date_expiration == date_alerte,
            Client.statut == 'actif'
        ).all()
        
        sujet = "Rappel : Votre abonnement expire bientôt"
        message = """Nous espérons que vous allez bien.
        
        Nous vous informons que votre abonnement expire dans 2 jours.
        N'hésitez pas à nous contacter pour le renouveler et continuer à bénéficier de nos services.
        
        Nous serions ravis de vous accompagner pour le renouvellement !"""
        
        for client in clients_a_alerter:
            success, result = envoyer_email(client.email, client.nom, sujet, message)
            
            # Enregistrer le log de l'email
            log = EmailLog(
                client_id=client.id,
                sujet=sujet,
                contenu=message,
                statut='envoyé' if success else 'échec'
            )
            db.session.add(log)
            db.session.commit()
            
            if success:
                print(f"Rappel d'expiration envoyé à {client.nom}")
            else:
                print(f"Erreur pour {client.nom}: {result}")

# Configuration du planificateur pour les rappels automatiques
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=envoyer_rappels_automatiques,
    trigger="interval",
    days=7,  # Vérifie chaque semaine
    id='rappels_automatiques'
)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('Connexion réussie!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Ce nom d\'utilisateur existe déjà.', 'error')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Cette adresse email est déjà utilisée.', 'error')
            return render_template('register.html', form=form)
        
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

@app.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Client.query
    
    # Filtrage par recherche
    if search:
        query = query.filter(
            or_(
                Client.nom.contains(search),
                Client.email.contains(search),
                Client.telephone.contains(search)
            )
        )
    
    # Filtrage par statut
    if status_filter:
        query = query.filter(Client.statut == status_filter)
    
    clients = query.all()
    
    # Calculer les alertes d'expiration
    today = datetime.now().date()
    for client in clients:
        if client.date_expiration:
            days_until_expiry = (client.date_expiration - today).days
            if days_until_expiry <= 2:
                client.alert_class = 'table-danger'
            elif days_until_expiry <= 7:
                client.alert_class = 'table-warning'
            else:
                client.alert_class = ''
        else:
            client.alert_class = ''
    
    return render_template('index.html', clients=clients, search=search, status_filter=status_filter, datetime=datetime)

@app.route('/ajouter_client', methods=['GET', 'POST'])
@login_required
def ajouter_client():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            nom=form.nom.data,
            email=form.email.data,
            telephone=form.telephone.data,
            date_derniere_visite=form.date_derniere_visite.data,
            date_expiration=form.date_expiration.data,
            notes=form.notes.data,
            statut=form.statut.data
        )
        db.session.add(client)
        db.session.commit()
        flash('Client ajouté avec succès!', 'success')
        return redirect(url_for('index'))
    return render_template('ajouter_client.html', form=form)

@app.route('/modifier_client/<int:id>', methods=['GET', 'POST'])
@login_required
def modifier_client(id):
    client = Client.query.get_or_404(id)
    form = ClientForm(obj=client)
    if form.validate_on_submit():
        form.populate_obj(client)
        db.session.commit()
        flash('Client modifié avec succès!', 'success')
        return redirect(url_for('index'))
    return render_template('modifier_client.html', form=form, client=client)

@app.route('/supprimer_client/<int:id>')
@login_required
def supprimer_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Client supprimé avec succès!', 'success')
    return redirect(url_for('index'))

@app.route('/envoyer_email/<int:id>', methods=['GET', 'POST'])
@login_required
def envoyer_email_client(id):
    client = Client.query.get_or_404(id)
    form = EmailForm()
    if form.validate_on_submit():
        success, result = envoyer_email(
            client.email, 
            client.nom, 
            form.sujet.data, 
            form.message.data
        )
        if success:
            flash('Email envoyé avec succès!', 'success')
        else:
            flash(f'Erreur lors de l\'envoi: {result}', 'error')
        return redirect(url_for('index'))
    sujet_prefill = request.args.get('sujet', '')
    message_prefill = request.args.get('message', '')
    return render_template('envoyer_email.html', form=form, sujet_prefill=sujet_prefill, message_prefill=message_prefill)

@app.route('/rappels_automatiques')
@login_required
def gerer_rappels():
    # Page pour gérer les rappels automatiques
    return render_template('rappels.html')

@app.route('/envoyer_rappels_maintenant')
@login_required
def envoyer_rappels_maintenant():
    envoyer_rappels_automatiques()
    flash('Rappels envoyés!', 'success')
    return redirect(url_for('gerer_rappels'))

@app.route('/signature', methods=['GET', 'POST'])
@login_required
def gerer_signature():
    form = SignatureForm()
    if form.validate_on_submit():
        if form.signature.data:
            filename = secure_filename('signature.png')
            signature_path = os.path.join('static', 'images', filename)
            form.signature.data.save(signature_path)
            flash('Signature mise à jour avec succès!', 'success')
            return redirect(url_for('gerer_signature'))
    
    # Vérifier si une signature existe
    signature_exists = os.path.exists(os.path.join('static', 'images', 'signature.png')) and \
                     os.path.getsize(os.path.join('static', 'images', 'signature.png')) > 0
    
    return render_template('signature.html', form=form, signature_exists=signature_exists)

# Route pour le dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Statistiques générales
    total_clients = Client.query.count()
    clients_actifs = Client.query.filter_by(statut='actif').count()
    clients_inactifs = Client.query.filter_by(statut='inactif').count()
    
    # Clients expirant bientôt
    today = datetime.now().date()
    expiring_soon = Client.query.filter(
        Client.date_expiration <= today + timedelta(days=7),
        Client.statut == 'actif'
    ).count()
    
    # Graphique des clients par statut
    statut_data = {
        'Actifs': clients_actifs,
        'Inactifs': clients_inactifs
    }
    
    # Graphique des ajouts par mois (6 derniers mois)
    six_months_ago = today - timedelta(days=180)
    clients_recent = Client.query.filter(Client.date_ajout >= six_months_ago).all()
    
    monthly_data = {}
    for client in clients_recent:
        month_key = client.date_ajout.strftime('%Y-%m')
        monthly_data[month_key] = monthly_data.get(month_key, 0) + 1
    
    # Emails envoyés (30 derniers jours)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    emails_sent = EmailLog.query.filter(
        EmailLog.date_envoi >= thirty_days_ago,
        EmailLog.statut == 'envoyé'
    ).count()
    
    return render_template('dashboard.html', 
                         total_clients=total_clients,
                         clients_actifs=clients_actifs,
                         clients_inactifs=clients_inactifs,
                         expiring_soon=expiring_soon,
                         statut_data=statut_data,
                         monthly_data=monthly_data,
                         emails_sent=emails_sent)

# Route pour l'export Excel
@app.route('/export/excel')
@login_required
def export_excel():
    clients = Client.query.all()
    
    # Créer un DataFrame pandas
    data = []
    for client in clients:
        data.append({
            'ID': client.id,
            'Nom': client.nom,
            'Email': client.email,
            'Téléphone': client.telephone or '',
            'Date d\'ajout': client.date_ajout.strftime('%d/%m/%Y') if client.date_ajout else '',
            'Date d\'expiration': client.date_expiration.strftime('%d/%m/%Y') if client.date_expiration else '',
            'Dernière visite': client.date_derniere_visite.strftime('%d/%m/%Y') if client.date_derniere_visite else '',
            'Statut': client.statut,
            'Notes': client.notes or ''
        })
    
    df = pd.DataFrame(data)
    
    # Créer le fichier Excel en mémoire
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Clients', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'clients_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

# Route pour l'export PDF
@app.route('/export/pdf')
@login_required
def export_pdf():
    clients = Client.query.all()
    
    # Créer le PDF en mémoire
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Données pour le tableau
    data = [['Nom', 'Email', 'Téléphone', 'Statut', 'Expiration']]
    
    for client in clients:
        data.append([
            client.nom,
            client.email,
            client.telephone or '',
            client.statut,
            client.date_expiration.strftime('%d/%m/%Y') if client.date_expiration else ''
        ])
    
    # Créer le tableau
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    doc.build([table])
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'clients_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

# Route pour les templates d'emails
@app.route('/templates')
@login_required
def templates():
    templates = EmailTemplate.query.all()
    return render_template('templates.html', templates=templates)

# Route pour ajouter un template
@app.route('/templates/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_template():
    if request.method == 'POST':
        nom = request.form['nom']
        sujet = request.form['sujet']
        contenu = request.form['contenu']
        
        template = EmailTemplate(nom=nom, sujet=sujet, contenu=contenu)
        db.session.add(template)
        db.session.commit()
        
        flash('Template ajouté avec succès!', 'success')
        return redirect(url_for('templates'))
    
    return render_template('ajouter_template.html')

# Route pour supprimer un template
@app.route('/templates/supprimer/<int:template_id>', methods=['DELETE'])
@login_required
def supprimer_template(template_id):
    template = EmailTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    return jsonify({'success': True})

# Route pour l'historique des emails
@app.route('/historique')
@login_required
def historique():
    page = request.args.get('page', 1, type=int)
    logs = EmailLog.query.order_by(EmailLog.date_envoi.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('historique.html', logs=logs)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
