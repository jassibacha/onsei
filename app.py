from flask import Flask, render_template, redirect, url_for, flash, request, session, g, abort, jsonify, current_app
import requests
import logging
import json
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, migrate, User
from forms import SignUpForm, LoginForm, UserEditForm
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from api_clients import *
from datetime import datetime, timedelta
from os import environ
from dotenv import load_dotenv

CURR_USER_KEY = "curr_user"
LIST_EXPIRY = 7

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

# Enable debug
app.debug = True

# Set up logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

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

    app.logger.debug('******* LOGIN STARTED *******')
    app.logger.debug('LIST LAST UPDATED AT: %s', user.anime_list_updated_at)
    app.logger.debug('CURRENT DATE/TIME: %s', datetime.utcnow())
    app.logger.debug('*****************************')

    # Check if profile is accessible (database field) and if the current list data is more than 7 days old
    if user.anilist_profile_accessible and (not user.anime_list_updated_at or datetime.utcnow() - user.anime_list_updated_at > timedelta(days=LIST_EXPIRY)):
    
        app.logger.debug("***** IT'S BEEN MORE THAN 7 DAYS. RE-FETCH LIST. *****")
        # Update anime list for user
        user.anime_list = fetch_user_anime_list(user.anilist_username, app)
        user.anime_list_updated_at = datetime.utcnow()

        # Commit the changes to the database
        db.session.commit()
    else:
        app.logger.debug("***** IT'S BEEN LESS THAN 7 DAYS. LIST IS GOOD. *****")



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
            app.logger.debug('Error is in Signup except')
            app.logger.debug(f"IntegrityError: {str(e)}")  # Add this line for debugging
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
            # user.anilist_username = form.anilist_username.data

            # Check if AniList username has been updated
            if user.anilist_username != form.anilist_username.data:
                # If it has, update it and check if it's public profile
                user.update_anilist_username(form.anilist_username.data)
            
                # If profile is accessible, refresh the anime list
                if user.anilist_profile_accessible:
                    user.anime_list = fetch_user_anime_list(user.anilist_username, app)
                    user.anime_list_updated_at = datetime.utcnow()
            

            db.session.commit()
            flash("Profile edited successfully!", 'success')
            return redirect(f"/profile")

        flash("Wrong password, try again.", 'danger')

    return render_template('users/edit-profile.html', form=form, user_id=user.id)

@app.route('/refresh-list', methods=['GET', 'POST'])
def refresh_list():
    """Refresh the anime list for the current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get(g.user.id)

    if not user.anilist_username:
        flash("No AniList username found.", "danger")
        return redirect("/profile")

    if not user.anilist_profile_accessible:
        flash("AniList profile is not accessible.", "danger")
        return redirect("/profile")

    # Update anime list for the user
    user.anime_list = fetch_user_anime_list(user.anilist_username, app)
    user.anime_list_updated_at = datetime.utcnow()

    # Commit the changes to the database
    db.session.commit()

    flash("Anime List successfully refreshed!", "success")
    return redirect("/profile")

@app.route('/profile/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()
    
    flash("Account deleted", "danger")
    return redirect("/signup")

##############################################################################
# App Routes
@app.route('/')
def search_form():
    """Search for a voice actor"""

    return redirect(url_for('va_search'))



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
        app.logger.debug('*** 200 CODE, RESPONSE IS GOOD ***')
        data = json.loads(response.text)
        va = data['data']['Page']['staff']
        return render_template('va-search.html', va=va, query=query)
    else:
        app.logger.debug('Request failed with status code:', response.status_code)
        app.logger.debug('Response:', response.text)

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
    response = make_api_request(va_query, variables, app)

    # Process the response
    if response is not None:
        va = response['data']['Staff']

        app.logger.debug('&&&&&&&&&&& RESPONSE FOR VA: &&&&&&&&&&&' )
        app.logger.debug(va)

        # Fetch all characterMedia series for the VA
        # character_media = fetch_all_character_media(va_id, app)


        # Check if user profile is accessible and anime_list isn't empty, if so fetch anime list
        anime_list = g.user.anime_list if g.user and g.user.anilist_profile_accessible and g.user.anime_list else None

        # Construct the output dictionary
        output = {
            'va': va
        }

        # If anime_list isn't empty, then add it to output
        if anime_list:
            output['anime_list'] = anime_list


        return render_template('va-details.html', va_id=va_id, output=output)

    return render_template('va-details.html', va_id=va_id)
    


@app.route('/api/character_media/<int:va_id>', methods=['GET'])
def get_character_media(va_id):
    """API Endpoint to fetch media + characters from a va's id and return json for front end"""
    data = fetch_all_character_media(va_id, app)
    return jsonify(data)


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


# Register the time_since filter as a decorator
@app.template_filter('time_since')
def time_since(dt):
    now = datetime.utcnow()
    diff = now - dt

    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


# Add the following lines to create the application context and call db.create_all()
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)