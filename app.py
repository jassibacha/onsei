from flask import Flask, render_template, redirect, url_for, flash, request
import requests
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

# Set the GraphQL endpoint URL
anilist_api_url = 'https://graphql.anilist.co'
# Set the request headers
anilist_api_headers = {'Content-Type': 'application/json'}

# Obtain Access Token
# token_url = ""
# data = {
#     "grant_type": "client_credentials",
#     "scope": "oapi"
# }
# Check .txt file for chatgpt oauth suggestions, for now we'll just use public data via open api connections


# Routes
@app.route('/')
def search_form():
    """Search for a voice actor"""

    return render_template('search-temp.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('va-search')

    # Perform the GraphQL query with the search query
    # Set the request data with the query
    data = {'query': f'''
        Page {{
            staff(search: "{query}") {{
                id
                name {{
                    first
                    last
                }}
                image {{
                    large
                    medium
                }}
                characters {{
                    nodes {{
                    name {{
                        full
                    }}
                    image {{
                        medium
                    }}
                    media {{
                        nodes {{
                        id
                            title {{
                            romaji
                            english
                            userPreferred
                            }}
                            coverImage {{
                            medium
                            color
                            }}
                        meanScore
                        popularity
                        trending
                        favourites
                        }}
                    }}
                    }}
                }}
            }}
        }}
        '''}

    # Send the GraphQL query to the AniList API
    response = requests.post(anilist_api_url, json=query, headers=anilist_api_headers)

    # Process the response
    if response.status_code == 200:
        data = json.loads(response.text)

        # Extract the search results from the response
        results = data['data']['Page']['media'] 
        print('***** WORKED! *****')
    else:
        print('Request failed with status code:', response.status_code)

    #data = json.loads(response.text)

    # Extract the search results from the response
    #results = data['data']['Page']['media'] 

    # Send the POST request to the AniList GraphQL endpoint
    #response = requests.post(url, json=data, headers=headers)


    # Return the search results to a template
    return render_template('results.html', query=query, results=results)

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