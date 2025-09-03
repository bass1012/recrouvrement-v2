from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FileField
from wtforms.validators import DataRequired

class EmailForm(FlaskForm):
    sujet = StringField('Sujet', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Envoyer')

class SignatureForm(FlaskForm):
    signature = FileField('Image de signature')
    submit = SubmitField('Télécharger')
