import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

class PasswordComplexity(object):
    def __init__(self, message=None):
        if not message:
            message = u'Password must include at least one of each: uppercase letter, lowercase letter, digit, and special character.'
        self.message = message

    def __call__(self, form, field):
        password = field.data
        if not (re.search(r'[A-Z]', password) and 
                re.search(r'[a-z]', password) and 
                re.search(r'\d', password) and 
                re.search(r'[@$!%*?&]', password)):
            raise ValidationError(self.message)


class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20), Regexp(r'^[\w.@+-]+$')])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8), PasswordComplexity()])
    # password = PasswordField('Password', validators=[DataRequired(), Length(min=8), Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$')])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    #submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    #submit = SubmitField('Log In')

# Regexp(r'^[\w.@+-]+$'):
# ^: Matches the start of the string.
# []: Character set, matches any single character within the brackets.
# \w: Matches any alphanumeric character or underscore.
# ., @, +, -: Matches the respective characters literally.
# $: Matches the end of the string.
# Overall, this regular expression ensures that the username field only contains alphanumeric characters, underscores, dots, at signs, plus signs, and hyphens.

# Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$'):
# ^: Matches the start of the string.
# (?=.*[a-z]): Positive lookahead assertion. Ensures that there is at least one lowercase letter.
# (?=.*[A-Z]): Positive lookahead assertion. Ensures that there is at least one uppercase letter.
# (?=.*\d): Positive lookahead assertion. Ensures that there is at least one digit.
# (?=.*[@$!%*?&]): Positive lookahead assertion. Ensures that there is at least one special character from the given set.
# [A-Za-z\d@$!%*?&]+: Matches one or more of the specified characters (letters, digits, and special characters).
# $: Matches the end of the string.
# Overall, this regular expression enforces a password policy that requires at least one lowercase letter, one uppercase letter, one digit, and one special character from the set @$!%*?&.

class UserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    anilist_username = StringField('AniList Username')
    password = PasswordField('Password', validators=[DataRequired()])
