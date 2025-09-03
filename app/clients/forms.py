from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email

class ClientForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telephone = StringField('Téléphone')
    date_derniere_visite = DateField('Date dernière visite')
    date_expiration = DateField('Date d\'expiration', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    statut = SelectField('Statut', choices=[('actif', 'Actif'), ('inactif', 'Inactif')])
    submit = SubmitField('Enregistrer')
