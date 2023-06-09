from flask import Flask, render_template, redirect, url_for, flash, request, session, g, abort, jsonify, current_app
import requests
import logging
import json
from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, migrate, User
from forms import SignUpForm, LoginForm, UserEditForm
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from api_clients import *
from datetime import datetime, timedelta
from dotenv import load_dotenv

CURR_USER_KEY = "curr_user"
LIST_EXPIRY = 7
ANILIST_API_URL = 'https://graphql.anilist.co'
ANILIST_API_HEADERS = {'Content-Type': 'application/json'}

app = Flask(__name__)
load_dotenv()
app.app_context().push()

# Contect Processor Function: This function will be called every time a template is rendered.
# The returned dictionary will be injected into the template's context, meaning its keys will become variables available in the template.
@app.context_processor
def inject_is_prod():
    # We're adding the 'is_prod' variable, which is True if the app is running in production.
    # This variable will be accessible in all templates, allowing us to conditionally add or remove things based on the environment.
    return dict(is_prod=app.config['ENV'] == 'production')


# Temp notes about render deploy attempts
# 1. I tried making a Procfile  REMOVED
# 2. I added app.app_context().push()
# 3. Manually specified a version of setuptools instead of letting it install as a dependency REMOVED

# Use ENV to decide which Config to use
if app.config['ENV'] == 'production':
    app.config.from_object(ProductionConfig)
elif app.config['ENV'] == 'development':
    app.config.from_object(DevelopmentConfig)
# else:
#     app.config.from_object(TestingConfig)

debug = DebugToolbarExtension(app)

# If DEBUG = True, setup logging
if app.debug:
    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)

# Call our connect_db function from models
connect_db(app)

# Initialize Flask-Migrate
migrate.init_app(app, db)

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

    # Send the search query to the AniList API
    response_data = search_voice_actors(query, app)
    print('RESPONSE DATA:', response_data)
    staff = response_data['data']['va']
    status_code = response_data['data']['status_code']

    if status_code != 200:
        flash(f'An error occurred when contacting the AniList API. (Status code: {status_code})')
        return render_template('va-search.html')

    # Filter the staff
    filtered_staff = []
    # Iterate over each voice actor in the staff list
    for va in staff:
        valid_characters = [character for character in va['characters']['nodes'] if 'id' in character and character['id'] != 36309]

        # valid_characters = [character for character in va['characters']['nodes'] if character['id'] != 36309]
        if valid_characters:
            va['characters']['nodes'] = valid_characters[:5]  # Limit the number of characters to 5
            filtered_staff.append(va)

    print('FILTERED STAFF:', filtered_staff)
    # Send the results to the search results page
    return render_template('va-search.html', staff=filtered_staff, query=query)


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
            yearsActive
            homeTown
            bloodType
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
            'va': va,
            'anime_list': anime_list if anime_list else [] # Empty list if anime_list not avail
        }

        # If anime_list isn't empty, then add it to output
        # if anime_list:
        #     output['anime_list'] = anime_list


        return render_template('va-details.html', va_id=va_id, output=output)

    return render_template('va-details.html', va_id=va_id)
    


@app.route('/api/character_media/<int:va_id>', methods=['GET'])
def get_character_media(va_id):
    """API Endpoint to fetch media + characters from a va's id and return json for front end"""
    token = request.headers.get('Authorization')
    # Not a secture token or anything since we're storing it in git and it's visible on the front end js calls, but it's something I guess.
    if not token or token != "Bearer wnYW3pY6b/pmAsNur?sbx=EOrTDKqslHIGjG":
        abort(403)
    data = fetch_all_character_media(va_id, app)
    return jsonify(data)


@app.route('/series/search', methods=['GET', 'POST'])
def series_search():
    
    query = request.form.get('series-search')
    print('QUERY:', query)

    if not query:
        # Display the search page without making a GraphQL query
        return render_template('series-search.html')

    # Send the GraphQL query to the AniList API
    response = search_anime_series(query, app)
    data = response["data"]

    app.logger.debug(f'*** SERIES SEARCH ROUTE. STATUS CODE: {data["status_code"]} ***')

    # Process the response
    if data['status_code'] == 200:
        app.logger.debug('*** 200 CODE, RESPONSE IS GOOD ***')
        series = data['series']
        return render_template('series-search.html', series=series, query=query)
    else:
        app.logger.debug(f'*** Request failed with status code: {data["status_code"]} ***')


    return render_template('series-search.html')

@app.route('/series/<int:series_id>', methods=['GET', 'POST'])
def series_details(series_id):
    """Grab the series details by AniList ID"""

    # Simplified query grabbing ONLY the seriesstaff info for the ID. No pagination needed. We're grabbing the series/character data in a separate call.
    series_query = '''
    query ($id: Int) {
		Media(id: $id) {
            title {
                english
                romaji
            }
            bannerImage
            coverImage {
                color
                large
            }
            description
            genres
            episodes
            idMal
            id
            season
            seasonYear
            studios {
                edges {
                    node {
                        name
                        id
                    }
                }
            }
            tags {
                name
                category
                id
            }
        }
    }
    '''

    # Variables, we literally only need ID here.
    variables = {
        'id': series_id,
    }

    # Send the GraphQL query to the AniList API
    response = make_api_request(series_query, variables, app)

    # Process the response
    if response is not None:
        series = response['data']['Media']

        app.logger.debug('&&&&&&&&&&& RESPONSE FOR SERIES: &&&&&&&&&&&' )
        app.logger.debug(series)

        # Fetch all characterMedia series for the VA
        # character_media = fetch_all_character_media(va_id, app)

        # Check if user profile is accessible and anime_list isn't empty, if so fetch anime list
        
        # Construct the output dictionary
        output = {
            'series': series
        }

        # If anime_list isn't empty, then add it to output
        # if anime_list:
        #     output['anime_list'] = anime_list


        return render_template('series-details.html', series_id=series_id, output=output)

    return render_template('series-details.html', series_id=series_id)


@app.route('/api/series_roles/<int:series_id>', methods=['GET'])
def get_series_roles(series_id):
    """API Endpoint to fetch characters & VA's from a series id and return json for front end"""
    token = request.headers.get('Authorization')
    # Not a secture token or anything since we're storing it in git and it's visible on the front end js calls, but it's something I guess.
    if not token or token != "Bearer wnYW3pY6b/pmAsNur?sbx=EOrTDKqslHIGjG":
        abort(403)
    data = fetch_series_characters_roles(series_id, app)
    return jsonify(data)


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
    # Use app.run() only when running locally
    app.run(debug=True)