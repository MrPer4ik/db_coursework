from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, RadioField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from re import match


from app.models import User, Pokemon

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], render_kw={"placeholder": "   Username"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "   Password"})
    remember_me = BooleanField('Remember Me', render_kw={"class": "checkbox"})
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], render_kw={"placeholder": "   Username"})
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"placeholder": "   Email"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "   Password"})
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')], render_kw={"placeholder": "   Repeat password"})
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
        if match(r"(?P<name>[\w\d._-]+)@(?P<domain>(([a-z0-9]+)\.)+[a-z]+)", email.data) is None:
            raise ValidationError("Please use a correct email adress.")

class EditingQuery(FlaskForm):
    choices = [('pokemon.pok_id', 'pokedex #'), ('base_stats.b_atk', 'ATK'), ('base_stats.b_hp', 'HP'),
            ('base_stats.b_def', 'DEF'), ('base_stats.b_sp_atk', 'SP.ATK'), ('base_stats.b_sp_def', 'SP.DEF'), ('base_stats.b_speed', 'SPD')]
    searchField = StringField('Search', render_kw={"placeholder": "   Search..."})
    sortedField = SelectField('Select sorted field', choices = choices, validators = [DataRequired()], default='pokemon.pok_id', render_kw={"class": "combobox"})
    filterField = RadioField('Label', choices=[('asc', 'Ascending'), ('desc', 'Descending')], default="asc", render_kw={"class": "radio"})
    submit = SubmitField('Accept')

class AddBuddy(FlaskForm):
    submit = SubmitField("Make this pokemon your buddy")
