from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from . import emails
from .. import db
from ..models import Client, EmailTemplate, EmailLog
from .forms import EmailForm, SignatureForm
from ..email import envoyer_email_func, envoyer_rappels_automatiques_func
import os
from werkzeug.utils import secure_filename

@emails.route('/envoyer_email/<int:id>', methods=['GET', 'POST'])
@login_required
def envoyer_email_client(id):
    client = Client.query.get_or_404(id)
    form = EmailForm()
    if form.validate_on_submit():
        success, result = envoyer_email_func(
            client.email, 
            client.nom, 
            form.sujet.data, 
            form.message.data
        )
        if success:
            flash('Email envoyé avec succès!', 'success')
        else:
            flash(f'Erreur lors de l\'envoi: {result}', 'error')
        return redirect(url_for('main.index'))
    sujet_prefill = request.args.get('sujet', '')
    message_prefill = request.args.get('message', '')
    return render_template('envoyer_email.html', form=form, sujet_prefill=sujet_prefill, message_prefill=message_prefill)

@emails.route('/rappels_automatiques')
@login_required
def gerer_rappels():
    return render_template('rappels.html')

@emails.route('/envoyer_rappels_maintenant')
@login_required
def envoyer_rappels_maintenant():
    envoyer_rappels_automatiques_func()
    flash('Rappels envoyés!', 'success')
    return redirect(url_for('.gerer_rappels'))

@emails.route('/signature', methods=['GET', 'POST'])
@login_required
def gerer_signature():
    form = SignatureForm()
    if form.validate_on_submit():
        if form.signature.data:
            filename = secure_filename('signature.png')
            signature_path = os.path.join('static', 'images', filename)
            form.signature.data.save(signature_path)
            flash('Signature mise à jour avec succès!', 'success')
            return redirect(url_for('.gerer_signature'))
    
    signature_exists = os.path.exists(os.path.join('static', 'images', 'signature.png')) and \
                     os.path.getsize(os.path.join('static', 'images', 'signature.png')) > 0
    
    return render_template('signature.html', form=form, signature_exists=signature_exists)

@emails.route('/templates')
@login_required
def templates():
    templates = EmailTemplate.query.all()
    return render_template('templates.html', templates=templates)

@emails.route('/templates/ajouter', methods=['GET', 'POST'])
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
        return redirect(url_for('.templates'))
    
    return render_template('ajouter_template.html')

@emails.route('/templates/supprimer/<int:template_id>', methods=['DELETE'])
@login_required
def supprimer_template(template_id):
    template = EmailTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    return jsonify({'success': True})

@emails.route('/historique')
@login_required
def historique():
    page = request.args.get('page', 1, type=int)
    logs = EmailLog.query.order_by(EmailLog.date_envoi.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('historique.html', logs=logs)
