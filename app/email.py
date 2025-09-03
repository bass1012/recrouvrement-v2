import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
from flask import current_app
from .models import Client, EmailLog
from . import db
from datetime import datetime, timedelta

def envoyer_email_func(destinataire_email, destinataire_nom, sujet, message):
    try:
        smtp_server = current_app.config['SMTP_SERVER']
        smtp_port = current_app.config['SMTP_PORT']
        email_expediteur = current_app.config['EMAIL_EXPEDITEUR']
        mot_de_passe = current_app.config['MOT_DE_PASSE_EMAIL']
        
        if not email_expediteur or not mot_de_passe:
            return False, "Configuration email manquante"
        
        msg = MIMEMultipart('related')
        msg['From'] = email_expediteur
        msg['To'] = destinataire_email
        msg['Subject'] = sujet
        
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        
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
        
        corps_texte = f"""
        Bonjour {destinataire_nom},
        
        {message}
        
        Cordialement,
        """
        
        msg_alternative.attach(MIMEText(corps_texte, 'plain', 'utf-8'))
        msg_alternative.attach(MIMEText(corps_html, 'html', 'utf-8'))
        
        signature_path = os.path.join('static', 'images', 'signature.png')
        if os.path.exists(signature_path) and os.path.getsize(signature_path) > 0:
            with open(signature_path, 'rb') as f:
                img_data = f.read()
                image = MIMEImage(img_data)
                image.add_header('Content-ID', '<signature>')
                image.add_header('Content-Disposition', 'inline', filename='signature.png')
                msg.attach(image)
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_expediteur, mot_de_passe)
        text = msg.as_string()
        server.sendmail(email_expediteur, destinataire_email, text)
        server.quit()
        
        return True, "Email envoyé avec succès"
        
    except Exception as e:
        return False, f"Erreur lors de l'envoi: {str(e)}"

def envoyer_rappels_automatiques_func():
    with current_app.app_context():
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
            success, result = envoyer_email_func(client.email, client.nom, sujet, message)
            
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
