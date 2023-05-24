from flask import Flask, render_template, redirect, url_for, flash, request, session, g, abort, jsonify, current_app
import requests
import json
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, migrate, User
from forms import SignUpForm, LoginForm, UserEditForm
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from api_clients import *
from os import environ
from dotenv import load_dotenv

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
# db = SQLAlchemy()
# migrate = Migrate(app, db)

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

# Call our connect_db function from models
connect_db(app)

# Initialize Flask-Migrate
migrate.init_app(app, db)

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

##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/test-db')
def test_db():
    """Test and confim database connection. DELETE THIS ON PRODUCTION!"""
    try:
        db.session.execute(text('SELECT 1'))
        return 'Database connection successful'
    except Exception as e:
        return f'Database connection failed: {str(e)}'




@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = SignUpForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data
            )
            db.session.commit()

        except IntegrityError as e:
            print('Error is in Signup except')
            print(f"IntegrityError: {str(e)}")  # Add this line for debugging
            flash(f"Signup Error: Already Taken {e}", 'danger')
            
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""
    do_logout()
    flash(f"Successfully logged out.", "danger")
    return redirect("/")

##############################################################################
# General user routes:

@app.route('/profile')
def profile_view():
    """Show user profile."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(g.user.id)
    
    return render_template('users/profile.html', user=user)

@app.route('/profile/edit', methods=["GET", "POST"])
def profile_edit():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    #print(g.user)
    
    user = g.user
    form = UserEditForm(obj=user)
    
    if form.validate_on_submit():
        # We grab user.username from user = g.user to auth it's correct user
        # We're also verifying the password here, password can't be changed
        if User.authenticate(user.username,form.password.data):
            # Now we can update username if we want
            user.username = form.username.data
            user.email = form.email.data

            db.session.commit()
            flash("Profile edited successfully!", 'success')
            return redirect(f"/profile")

        flash("Wrong password, try again.", 'danger')

    return render_template('users/edit-profile.html', form=form, user_id=user.id)


##############################################################################
# App Routes
@app.route('/')
def search_form():
    """Search for a voice actor"""

    return render_template('search-temp.html')


@app.route('/search', methods=['GET', 'POST'])
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
        # Add the data to session so we can pull it in va-select if necessary
        # session['search_data'] = data

        # Add the search query to session quickly
        session['va_query'] = query

        # Extract the search results from the response
        staff_list = data['data']['Page']['staff']
        staff_count = len(staff_list)
        ###
        ### SHOULD I JUST DO A BASIC PARSE, SEE IF THERES MORE THAN 1, THEN DO A DETAILED PARSE FROM THERE?
        ###
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



@app.route('/va/search', methods=['GET', 'POST'])
def va_search():
    
    query = request.form.get('va-search')
    print('QUERY:', query)

    if not query:
        # Display the search page without making a GraphQL query
        return render_template('va-search.html')

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
        print ('*** 200 CODE, RESPONSE IS GOOD ***')
        data = json.loads(response.text)
        va = data['data']['Page']['staff']
        return render_template('va-search.html', va=va, query=query)
    else:
        print('Request failed with status code:', response.status_code)
        print('Response:', response.text)

    return render_template('va-search.html')


@app.route('/va/<int:va_id>', methods=['GET', 'POST'])
def va_details(va_id):
    """Grab the VA details by AniList ID"""

    # Simplified query grabbing ONLY the staff info for the ID. No pagination needed. We're grabbing the series/character data in a separate call.
    va_query = '''
    query ($id: Int) {
        Staff(id: $id) {
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
            languageV2
            description
            gender
            primaryOccupations
            dateOfBirth {
                year
                month
                day
            }
            dateOfDeath {
                year
                month
                day
            }
            age
        }
    }
    '''

    # Variables, we literally only need ID here.
    variables = {
        'id': va_id,
    }

    # Send the GraphQL query to the AniList API
    response = make_api_request(va_query, variables)

    # Process the response
    if response is not None:
        va = response['data']['Staff']

        print('&&&&&&&&&&& RESPONSE FOR VA: &&&&&&&&&&&' )
        print(va)

        # Fetch all characterMedia series for the VA
        character_media = fetch_all_character_media(va_id)

        # Construct the output dictionary
        output = {
            'va': va,
            'characterMedia': character_media
        }

        return render_template('va-details.html', output=output)

    return render_template('va-details.html', va_id=va_id)
    


    #    va = data['data']['Page']['staff'][0]


# @app.route('/va/<int:va_id>', methods=['GET', 'POST'])
# def va_details(va_id):
#     """Grab the VA details by AniList ID"""

#     # Perform the GraphQL query with the search query
#     graphql_query = '''
#     query ($page: Int, $perPage: Int, $id: Int) {
#         Page(page: $page, perPage: $perPage) {
#             pageInfo {
#                 total
#                 currentPage
#                 lastPage
#                 hasNextPage
#                 perPage
#             }
#             staff(id: $id) {
#                 id
#                 name {
#                     first
#                     last
#                     full
#                 }
#                 image {
#                     large
#                     medium
#                 }
#                 languageV2
#                 description
#                 gender
#                 primaryOccupations
#                 age
#                 characterMedia {
#                     edges {
#                         node {
#                             id
#                             idMal
#                             title {
#                                 romaji
#                                 english
#                                 userPreferred
#                             }
#                             type
#                             seasonYear
#                             coverImage {
#                                 large
#                                 medium
#                                 color
#                             }
#                             meanScore
#                             popularity
#                             trending
#                             favourites
#                         }
#                         characters {
#                             id
#                             name {
#                                 full
#                             }
#                             image {
#                                 large
#                                 medium
#                             }
#                         }
#                     }
#                 }
#             }
#         }
#     }
#     '''

#     variables = {
#         'id': va_id,
#         #'search': query,
#         'page': 1,
#         'perPage': 50
#     }

#     # Send the GraphQL query to the AniList API
#     response = requests.post(anilist_api_url, json={'query': graphql_query, 'variables': variables}, headers=anilist_api_headers)


#     # Process the response
#     if response.status_code == 200:
#         print('*** VA DETAILS - 200 CODE, RESPONSE IS GOOD ***')
#         data = json.loads(response.text)
#         #print(data)
#         # We need to grab the first list item in the results, even though there's only one result because we're pulling from ID!
#         va = data['data']['Page']['staff'][0]

#         # Handle dateOfBirth
#         date_of_birth = va.get('dateOfBirth')
#         if date_of_birth:
#             birth_year = date_of_birth.get('year')
#             birth_month = date_of_birth.get('month')
#             birth_day = date_of_birth.get('day')
#             va['dateOfBirth'] = f"{birth_year}-{birth_month}-{birth_day}"

#         # Handle dateOfDeath
#         date_of_death = va.get('dateOfDeath')
#         if date_of_death:
#             death_year = date_of_death.get('year')
#             death_month = date_of_death.get('month')
#             death_day = date_of_death.get('day')
#             va['dateOfDeath'] = f"{death_year}-{death_month}-{death_day}"

#         print('VA ID: ', va_id, 'VA RETURN: ', va)
#         return render_template('va-details.html', va=va)
#     else:
#         print('Request failed with status code:', response.status_code)
#         print('Response:', response.text)

#     return render_template('va-details.html', va_id=va_id)


@app.route('/select-va', methods=['GET', 'POST'])
def select_va():

    #########
    ## DO WE NEED TO SPLIT THIS ROUTE? OR AT LEAST AN IF STATEMENT BETWEEN GET AND POST
    ## GET SHOULD BE GRABBING THE EXISTING JSON DATA FROM QUERY
    ## POST SHOULD BE SUBMITTING THE VA ID TO VA_DETAILS
    #########

    
    print('*****PRE IF STATEMENT*****')
    if request.method == 'GET':
        print('*****ITS A GET REQUEST*****')
        # We have a GET request, which means we need to display multiple VA's and select one.

        # Check if 'search_data' exists in the session
        # if 'search_data' not in session:
        #     # Handle the case where 'search_data' is not present
        #     flash('Search data not found', 'error')
        #     return redirect(url_for('search'))

        # Grab the search_data sesssion from /search page
        data = session.get('search_data')
        print('data from sesion', data)

        va = data['data']['Page']['staff']
        return render_template('select-va.html', query=query, va=va)

        # # Send the GraphQL query to the AniList API
        # response = requests.post(anilist_api_url, json={'query': graphql_query, 'variables': variables}, headers=anilist_api_headers)
        
        # ## GET SHOULD BE GRABBING THE EXISTING JSON DATA FROM QUERY AND DISPLAYING
        # if response.status_code == 200:

        #     print('*****RESPONSE STATUS 200*****')
        #     data = json.loads(response.text)
        #     print('*****DATA PAGE STAFF*****')
        #     print(data['data']['Page']['staff'])
        #     va = data['data']['Page']['staff']
        #     return render_template('select-va.html', query=query, va=va)
        # #return render_template('select-va.html', va_id=va_id, query=query)
        # else:
        #     print('GET Request failed with status code:', response.status_code)
        #     print('Response:', response.text)
        #     return render_template('error.html', message='Failed to retrieve VA details')

    # elif request.method == 'POST':

        # Grab these two values which are used in variables for the graphql query
        #va_id = request.form.get('va-id')
        #query = request.form.get('va-search')



        # Perform the GraphQL query with the search query
        # graphql_query = '''
        # query ($page: Int, $perPage: Int, $search: String) {
        #     Page(page: $page, perPage: $perPage) {
        #         pageInfo {
        #             total
        #             currentPage
        #             lastPage
        #             hasNextPage
        #             perPage
        #         }
        #         staff(search: $search) {
        #             id
        #             name {
        #                 first
        #                 last
        #                 full
        #             }
        #             image {
        #                 large
        #                 medium
        #             }
        #             characters (perPage: 3) {
        #                 nodes {
        #                     name {
        #                         full
        #                     }
        #                     image {
        #                         medium
        #                     }
        #                     media {
        #                         nodes {
        #                         id
        #                             title {
        #                                 romaji
        #                                 english
        #                                 userPreferred
        #                             }
        #                             coverImage {
        #                                 medium
        #                                 color
        #                             } 
        #                             meanScore
        #                             popularity
        #                             trending
        #                             favourites
        #                         }
        #                     }
        #                 }
        #             }
        #         }
        #     }
        # }
        # '''

        # variables = {
        #     #'id': va_id,
        #     'search': query,
        #     'page': 1,
        #     #'perPage': 10
        # }


    #     # Handle the POST request
    #     # va_id = request.form.get('va-id')
    #     # query = request.form.get('va-search')

        
    #     # Perform the necessary operations for the POST request
    #     # ...

    #     ## POST SHOULD BE RE-SUBMITTING SEARCH QUERY, BUT FROM THE SELECT-VA PAGE
        
    #     # Redirect to the va_details route with the appropriate va_id
    #     return redirect(url_for('va_details', va_id=va_id))

    

    # # Process the response
    # if response.status_code == 200:
    #     data = json.loads(response.text)
    #     print('*****DATA*****')
    #     print(data)
    #     print('*****DATA PAGE STAFF*****')
    #     print(data['data']['Page']['staff'])
    #     # print('*****DATA STAFF*****')
    #     # print(data['staff'])
    #     va = data['data']['Page']['staff']
    #     # va = data['data']['staff']
    #     return render_template('va-details.html', va=va)
    # else:
    #     print('Request failed with status code:', response.status_code)
    #     print('Response:', response.text)
    #     return render_template('error.html', message='Failed to retrieve VA details')




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

# Add the following lines to create the application context and call db.create_all()
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)