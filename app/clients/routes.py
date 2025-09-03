from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from . import clients
from .. import db
from ..models import Client
from .forms import ClientForm

@clients.route('/ajouter_client', methods=['GET', 'POST'])
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
        return redirect(url_for('main.index'))
    return render_template('ajouter_client.html', form=form)

@clients.route('/modifier_client/<int:id>', methods=['GET', 'POST'])
@login_required
def modifier_client(id):
    client = Client.query.get_or_404(id)
    form = ClientForm(obj=client)
    if form.validate_on_submit():
        form.populate_obj(client)
        db.session.commit()
        flash('Client modifié avec succès!', 'success')
        return redirect(url_for('main.index'))
    return render_template('modifier_client.html', form=form, client=client)

@clients.route('/supprimer_client/<int:id>')
@login_required
def supprimer_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Client supprimé avec succès!', 'success')
    return redirect(url_for('main.index'))
