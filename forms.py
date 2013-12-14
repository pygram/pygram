import re

from wtforms import Form, TextAreaField, TextField, SelectField
from wtforms import validators as v
from wtforms import ValidationError




class AnalyzeGrammarForm(Form):

    def terminals_check(form, field):
        if re.match(r'^[a-zA-Z0-9\s]+$',field.data) is None:
            raise ValidationError('Bad input: invalid characters found.')

    def productions_check(form, field):
         if re.match(r'^[a-zA-Z0-9\s\|\:\;]+$',field.data) is None:
            raise ValidationError('Bad input: invalid characters found.')

    type = SelectField('Type', choices=[('SLR', 'SRL(1)'), ('LALR', 'LALR(1)')])
    start = TextField('Start symbol', [v.Optional(), terminals_check])
    terminals = TextAreaField('Terminals', [v.Required(), terminals_check])
    productions = TextAreaField('Productions', [v.Required(), productions_check])
