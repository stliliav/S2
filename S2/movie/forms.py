from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, IntegerField
from wtforms.validators import DataRequired

class MovieForm(FlaskForm):
    title = StringField('Movie name', validators=[DataRequired()])
    genres = StringField('Genres', validators=[DataRequired()])
    year = IntegerField('Year of publishing', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    img = FileField('Image')
    submit = SubmitField('Save movie')