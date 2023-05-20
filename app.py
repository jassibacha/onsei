from flask import Flask, render_template, redirect, url_for, flash, request
import requests
import json
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
    graphql_query = '''
    query ($page: Int, $perPage: Int, $search: String) {
        Page(page: $page, perPage: $perPage) {
            pageInfo {
                total
                currentPage
                lastPage
                hasNextPage
                perPage
            }
            staff(search: $search) {
                id
                name {
                    first
                    last
                    full
                }
                image {
                    large
                    medium
                }
                characters (perPage: 3) {
                    nodes {
                        name {
                            full
                        }
                        image {
                            medium
                        }
                        media {
                            nodes {
                            id
                                title {
                                    romaji
                                    english
                                    userPreferred
                                }
                                coverImage {
                                    medium
                                    color
                                } 
                                meanScore
                                popularity
                                trending
                                favourites
                            }
                        }
                    }
                }
            }
        }
    }
    '''

    variables = {
        'search': query,
        'page': 1,
        #'perPage': 1
    }

    # Send the GraphQL query to the AniList API
    response = requests.post(anilist_api_url, json={'query': graphql_query, 'variables': variables}, headers=anilist_api_headers)

    # Process the response
    if response.status_code == 200:
        data = json.loads(response.text)

        # Extract the search results from the response
        staff_list = data['data']['Page']['staff']
        staff_count = len(staff_list)

        if staff_count > 1:
            print('More than one VA found, go to select_va')
            return redirect(url_for('select_va', query=query))
        elif staff_count == 1:
            print('Single staff found, go to va details page, VA: ')
            va = staff_list[0]
            print(va)
            va_id = staff_list[0]['id']
            return render_template('va-details.html', va=va)
            # return redirect(url_for('va_details', va=va))
        else:
            results = []
            return render_template('no-results.html', query=query)
    else:
        print('Request failed with status code:', response.status_code)
        print('Response:', response.text)
        results = []

    return render_template('results-temp.html', query=query, results=results)


@app.route('/select-va', methods=['GET', 'POST'])
def select_va():
    va_id = request.form.get('va-id')
    query = request.form.get('va-search')


    #########
    ## DO WE NEED TO SPLIT THIS ROUTE? OR AT LEAST AN IF STATEMENT BETWEEN GET AND POST
    ## GET SHOULD BE GRABBING THE EXISTING JSON DATA FROM QUERY
    ## POST SHOULD BE SUBMITTING THE VA ID TO VA_DETAILS
    #########

    # Perform the GraphQL query with the search query
    graphql_query = '''
    query ($page: Int, $perPage: Int, $search: String) {
        Page(page: $page, perPage: $perPage) {
            pageInfo {
                total
                currentPage
                lastPage
                hasNextPage
                perPage
            }
            staff(search: $search) {
                id
                name {
                    first
                    last
                    full
                }
                image {
                    large
                    medium
                }
                characters (perPage: 3) {
                    nodes {
                        name {
                            full
                        }
                        image {
                            medium
                        }
                        media {
                            nodes {
                            id
                                title {
                                    romaji
                                    english
                                    userPreferred
                                }
                                coverImage {
                                    medium
                                    color
                                } 
                                meanScore
                                popularity
                                trending
                                favourites
                            }
                        }
                    }
                }
            }
        }
    }
    '''

    variables = {
        'id': va_id,
        'search': query,
        'page': 1,
        'perPage': 5
    }

    # Send the GraphQL query to the AniList API
    response = requests.post(anilist_api_url, json={'query': graphql_query, 'variables': variables}, headers=anilist_api_headers)

    # Process the response
    if response.status_code == 200:
        data = json.loads(response.text)
        print('*****DATA*****')
        print(data)
        print('*****DATA PAGE STAFF*****')
        print(data['data']['Page']['staff'])
        # print('*****DATA STAFF*****')
        # print(data['staff'])
        va = data['data']['Page']['staff']
        # va = data['data']['staff']
        return render_template('va-details.html', va=va)
    else:
        print('Request failed with status code:', response.status_code)
        print('Response:', response.text)
        return render_template('error.html', message='Failed to retrieve VA details')




# @app.route('/search', methods=['POST'])
# def search():
#     query = request.form.get('va-search')

#     # Perform the GraphQL query with the search query
#     # Set the request data with the query
#     data = {'query': f'''
#         Page {{
#             staff(search: "{query}") {{
#                 id
#                 name {{
#                     first
#                     last
#                 }}
#                 image {{
#                     large
#                     medium
#                 }}
#                 characters {{
#                     nodes {{
#                     name {{
#                         full
#                     }}
#                     image {{
#                         medium
#                     }}
#                     media {{
#                         nodes {{
#                         id
#                             title {{
#                             romaji
#                             english
#                             userPreferred
#                             }}
#                             coverImage {{
#                             medium
#                             color
#                             }}
#                         meanScore
#                         popularity
#                         trending
#                         favourites
#                         }}
#                     }}
#                     }}
#                 }}
#             }}
#         }}
#         '''}

#     # Send the GraphQL query to the AniList API
#     response = requests.post(anilist_api_url, json=query, headers=anilist_api_headers)

#     # Process the response
#     if response.status_code == 200:
#         data = json.loads(response.text)

#         # Extract the search results from the response
#         results = data['data']['Page']['media'] 
#         print('***** WORKED! *****')
#     else:
#         print('Request failed with status code:', response.status_code)

#     #data = json.loads(response.text)

#     # Extract the search results from the response
#     #results = data['data']['Page']['media'] 

#     # Send the POST request to the AniList GraphQL endpoint
#     #response = requests.post(url, json=data, headers=headers)


#     # Return the search results to a template
#     return render_template('results.html', query=query, results=results)

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