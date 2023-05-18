from flask import Flask, render_template, redirect, url_for, flash, request
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from forms import RegisterForm
from os import environ
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = environ.get('SECRET_KEY')

# Having the Debug Toolbar show redirects explicitly is often useful;
# however, if you want to turn it off, you can uncomment this line:
#
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


# Routes
@app.route('/')
def temp():
    """Temporary page for testing stuff"""
    
    return render_template('temp.html')
# @app.route('/', methods=['GET', 'POST'])
# def register():
#     form = RegisterForm()
#     if form.validate_on_submit():
#         hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
#         # Save the user to the database
#         # You'll need to define a User model with the necessary fields (id, username, password, email, etc.)
#         user = User(username=form.username.data, password=hashed_password, email=form.email.data)
#         db.session.add(user)
#         db.session.commit()
#         flash('Account created successfully!', 'success')
#         return redirect(url_for('login'))
#     return render_template('register.html', form=form)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     # Implement your login logic here
#     return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)