# Testing via Terminal
# export ENV=testing
# python -m unittest discover -s tests

import os
import unittest
from unittest import TestCase
from models import db, User
from app import app
from datetime import datetime


class RoutesTestCase(TestCase):

    def create_app(self):
        app.config['ENV'] = 'testing'
        #app.config['SECRET_KEY'] = 'notsosecret'
        #app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///onsei-test'  # Use an in-memory SQLite database for testing
        return app

    def setUp(self):
        db.drop_all()
        db.create_all()

        self.user = User.signup('testuser', 'testuser@example.com', 'Password8784$$')
        self.user.anilist_username = 'hopesix'
        self.user.anilist_profile_accessible = True
        self.user.anime_list = {
            21366: {"status": "COMPLETED", "score": 9},
            98478: {"status": "COMPLETED", "score": 10},
            9624: {"status": "COMPLETED", "score": 7},
            100526: {"status": "COMPLETED", "score": 5},
            21711: {"status": "COMPLETED", "score": 8},
            98251: {"status": "COMPLETED", "score": 7},
            21058: {"status": "COMPLETED", "score": 7},
            20613: {"status": "COMPLETED", "score": 7},
            20770: {"status": "COMPLETED", "score": 8},
            47: {"status": "COMPLETED", "score": 7},
            100645: {"status": "COMPLETED", "score": 6}
        }
        self.user.anime_list_updated_at = datetime.utcnow()
        db.session.commit()

        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.remove()
        User.query.delete()
        db.session.commit()
        db.drop_all()
        self.app_context.pop()
    
    def test_index(self):
        """ Does index route work """
        with self.client as c:
            resp = c.get('/', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Onsei', str(resp.data))

    def test_signup(self):
        """ Does signup work """

        with self.client as c: 
            resp = c.get('/signup')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Sign Up', str(resp.data))

        with self.client as c: 
            form_data = {
                'username': 'testuser1', 
                'email': 'testuser1@test.com', 
                'password': 'TestPassword8723@(**',
                'confirm_password': 'TestPassword8723@(**'}
            resp = c.post('/signup', data=form_data, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Signup Successful', str(resp.data))

    def test_failed_signup_weakpass(self):
        """ Fail signup with a weak password """

        with self.client as c: 
            resp = c.get('/signup')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Sign Up', str(resp.data))

        with self.client as c: 
            form_data = {
                'username': 'testuser1', 
                'email': 'testuser1@test.com', 
                'password': 'weakpass',
                'confirm_password': 'weakpass'}
            resp = c.post('/signup', data=form_data, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Password must include at least one of each', str(resp.data))

    def test_login(self):
        """ Ensures login works """

        with self.client as c:
            resp = c.get('/login')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Login', str(resp.data))

        with self.client as c: 
            form_data = {'username': 'testuser', 'password': 'Password8784$$'}
            resp = c.post('/login', data=form_data, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Logout', str(resp.data)) #Confirm Logout button

    def test_failed_login(self):
        """ Ensures login fails accordingly when given incorrect password """

        with self.client as c: 
            form_data = {'username': 'testuser5', 'password': 'wrongpassword'}
            resp = c.post('/login', data=form_data, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Unsuccessful login', str(resp.data))

    def test_logout(self):
        """ Ensures logout works """

        with self.client as c:
            resp = c.get('/login')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Login', str(resp.data))

        with self.client as c: 
            form_data = {'username': 'testuser', 'password': 'Password8784$$'}
            resp = c.post('/login', data=form_data, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Logout', str(resp.data))

        with self.client as c: 
            resp = c.get('/logout', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Successfully logged out', str(resp.data))

    def test_profile_edit(self):
        """ Does viewing & editing profile work """    

        # return unauthorized message when user is not logged in

        with self.client as c:
            resp = c.get('/profile', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))   

        # log user in

        with self.client as c:
            form_data = {'username': 'testuser', 'password': 'Password8784$$'}
            resp = c.post('/login', data=form_data, follow_redirects=True)

        # Now we can view profile

        with self.client as c:
            resp = c.get('/profile', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Your Profile', str(resp.data)) 

        # ensures the edit is allowed when user is logged in and the information is updated correctly

        with self.client as c:
            form_data =  {'username': 'testuser', 'email': 'testuser2@test.com', 'password': 'Password8784$$', 'anilist_username': 'WhaleJucs'}
            resp = c.post('/profile/edit', data=form_data, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Profile edited successfully!', str(resp.data))
        
            updated_user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(updated_user)
            self.assertEqual(updated_user.anilist_username, 'WhaleJucs')

    def test_refresh_list(self):
        """ Can we refresh list? """    

        # log user in
        with self.client as c:
            form_data = {'username': 'testuser', 'password': 'Password8784$$'}
            resp = c.post('/login', data=form_data, follow_redirects=True)

        # Now we can view profile
        with self.client as c:
            resp = c.get('/refresh-list', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Anime List successfully refreshed!', str(resp.data)) 

    def test_fail_refresh_list(self):
        """ Get a fail response for an incorrect anilist username """    

        # log user in
        with self.client as c:
            form_data = {'username': 'testuser', 'password': 'Password8784$$'}
            resp = c.post('/login', data=form_data, follow_redirects=True)

        with self.client as c:
            form_data =  {'username': 'testuser', 'email': 'testuser2@test.com', 'password': 'Password8784$$', 'anilist_username': 'brokenName98345334xxx'}
            resp = c.post('/profile/edit', data=form_data, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Profile edited successfully!', str(resp.data))

        # Now we can view profile
        with self.client as c:
            resp = c.get('/refresh-list', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('AniList profile is not accessible.', str(resp.data)) 

    def test_va_search(self):
        """Does the voice actor search work?"""

        with self.client as c:
            # Prepare the data for the POST request
            form_data = {'va-search': 'Nakai'}

            # Send the POST request
            resp = c.post('/va/search', data=form_data, follow_redirects=True)

            # Check the response
            self.assertEqual(resp.status_code, 200)
            # Include more checks here based on the response data you expect
            self.assertIn('Search Results', str(resp.data)) 
            self.assertIn('Kazuya Nakai', str(resp.data)) 

    def test_va_details(self):
        """ Does the VA details page work? This can only check the initial python call, not the dynamic JS loading in later. """

        with self.client as c:
            resp = c.get('/va/100938', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Ayuru Ohashi', str(resp.data)) 


    def test_series_search(self):
        """Does the series search work?"""

        with self.client as c:
            # Prepare the data for the POST request
            form_data = {'series-search': 'Demon Slayer'}

            # Send the POST request
            resp = c.post('/series/search', data=form_data, follow_redirects=True)

            # Check the response
            self.assertEqual(resp.status_code, 200)
            # Include more checks here based on the response data you expect
            self.assertIn('Search Results', str(resp.data)) 
            self.assertIn('Demon Slayer: Kimetsu no Yaiba', str(resp.data)) 

    def test_series_details(self):
        """ Does the series details page work? This can only check the initial python call, not the dynamic JS loading in later. """

        with self.client as c:
            resp = c.get('/series/101922', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Kimetsu no Yaiba', str(resp.data)) 
            self.assertIn('SPRING', str(resp.data)) 

    def test_get_series_roles(self):
        """Test our API endpoint to pull data for a series to front-end"""

        with self.client as c:
            # Send the GET request
            resp = c.get('/api/series_roles/101922', headers={'Authorization': 'Bearer wnYW3pY6b/pmAsNur?sbx=EOrTDKqslHIGjG'})

            # Check the response
            self.assertEqual(resp.status_code, 200)

            # Load the JSON data from the response
            data = resp.get_json()

            # Check that data is a list
            self.assertIsInstance(data, list)

            # For each object in the list, only checking first 5
            for role in data[:5]:
                # Check that each role object has the correct fields
                self.assertIn('node', role)
                self.assertIn('role', role)
                self.assertIn('voiceActors', role)

                # For each voiceActor in the voiceActors array, only checking first voiceActor
                for voiceActor in role['voiceActors'][:1]:
                    # Check that each voiceActor object has the correct fields
                    self.assertIn('characters', voiceActor)
                    self.assertIn('id', voiceActor)
                    self.assertIn('image', voiceActor)
                    self.assertIn('name', voiceActor)
                    self.assertIn('full', voiceActor['name'])
                    self.assertIn('large', voiceActor['image'])
                    self.assertIn('medium', voiceActor['image'])

                    # Check that characters is a dictionary
                    self.assertIsInstance(voiceActor['characters'], dict)
                    
                    # Check that nodes is a list
                    self.assertIsInstance(voiceActor['characters']['nodes'], list)

                    # For each character in the nodes array, only checking first character
                    for character in voiceActor['characters']['nodes'][:1]:
                        # Check that each character object has the correct fields
                        self.assertIn('id', character)
                        self.assertIn('image', character)
                        self.assertIn('name', character)
                        self.assertIn('full', character['name'])
                        self.assertIn('large', character['image'])
                        self.assertIn('medium', character['image'])

    def test_get_character_media(self):
        """Can we get character media?"""

        with self.client as c:
            # Send the GET request
            resp = c.get('/api/character_media/111635', headers={'Authorization': 'Bearer wnYW3pY6b/pmAsNur?sbx=EOrTDKqslHIGjG'})

            # Check the response
            self.assertEqual(resp.status_code, 200)

            # Load the JSON data from the response
            data = resp.get_json()

            # Check that data is a list
            self.assertIsInstance(data, list)

            # For each object in the list, only checking first 5
            for media in data[:5]:
                # Check that each media object has the correct fields
                self.assertIn('characters', media)
                self.assertIn('node', media)

                # Check that characters is a list
                self.assertIsInstance(media['characters'], list)
                
                # For each character in the characters list
                for character in media['characters'][:1]:
                    # Check that each character object has the correct fields
                    self.assertIn('id', character)
                    self.assertIn('image', character)
                    self.assertIn('name', character)
                    self.assertIn('full', character['name'])
                    self.assertIn('large', character['image'])
                    self.assertIn('medium', character['image'])

                # Check that node is a dictionary
                self.assertIsInstance(media['node'], dict)

                # Check that each node object has the correct fields
                self.assertIn('averageScore', media['node'])
                self.assertIn('coverImage', media['node'])
                self.assertIn('favourites', media['node'])
                self.assertIn('id', media['node'])
                self.assertIn('idMal', media['node'])
                self.assertIn('meanScore', media['node'])
                self.assertIn('popularity', media['node'])
                self.assertIn('seasonYear', media['node'])
                self.assertIn('title', media['node'])
                self.assertIn('trending', media['node'])
                self.assertIn('type', media['node'])
                self.assertIn('english', media['node']['title'])
                self.assertIn('romaji', media['node']['title'])
                self.assertIn('userPreferred', media['node']['title'])
                self.assertIn('color', media['node']['coverImage'])
                self.assertIn('large', media['node']['coverImage'])
                self.assertIn('medium', media['node']['coverImage'])

    def test_404_route(self):
        """Check for a 404"""
        with self.client as c:
            resp = c.get('/nonexistentroute')
            self.assertEqual(resp.status_code, 404)