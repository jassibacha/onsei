from flask import flash
import requests, json


def make_api_request(query, variables, app):

    # Set the GraphQL endpoint URL
    anilist_api_url = 'https://graphql.anilist.co'

    # Set the request headers
    anilist_api_headers = {'Content-Type': 'application/json'}

    # log the request details
    app.logger.debug(f"**************************************")
    app.logger.debug(f"**************************************")
    app.logger.debug(f"API request: {query}, {variables}")

    response = requests.post(anilist_api_url, json={'query': query, 'variables': variables}, headers=anilist_api_headers)

    # log the response
    app.logger.debug(f"API response: {response}")
    app.logger.debug(f"**************************************")
    app.logger.debug(f"**************************************")

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        app.logger.debug('MAKE API REQUEST returned 404 status code: %s', response.status_code)
        app.logger.debug('Response: %s', response.text)
        return response.json()  # return the JSON response even though the status was 404
    else:
        app.logger.debug('MAKE API REQUEST Failed with status code: %s', response.status_code)
        app.logger.debug('Response: %s', response.text)
        return None


def search_voice_actors(search_query, app):
    """Fetch all voice actors based on search query"""

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

    graphql_query3 = '''
    query GetVA($page: Int, $perPage: Int, $search: String) {
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
					full
                }
                image {
                    large
                    medium
                }
				characters(page: 1, perPage: 6, sort:FAVOURITES_DESC) {
					nodes {
						id
						name {
							full
						}
                        image {
                            medium
                        }
						favourites
					}
				}
			}
		}
    }
    '''
    # media(sort: FAVOURITES_DESC) {
    #     nodes {
    #         id
    #         title {
    #             english
    #             romaji
    #         }
    #         type
    #         favourites
    #     }
    # }

    # Variables for the GraphQL query
    variables = {
        'search': search_query,
        'page': 1,
        'perPage': 50
    }

    # Make the initial API request
    response = make_api_request(graphql_query3, variables, app)

    app.logger.debug(f'*** SEARCH VOICE ACTORS: {search_query} ***')

    if response is not None:
        app.logger.debug('***** RESPONSE IS NOT NONE *****')
        search_staff = response['data']['Page']
        all_staff = search_staff['staff']

        # Fetch additional pages if available
        while search_staff['pageInfo']['hasNextPage']:
            app.logger.debug("*** NEXT PAGE AVAIL, +1 PAGE AND REQUEST API AGAIN ***")
            variables['page'] += 1
            app.logger.debug(f"*** PAGE {variables['page']} OF {search_staff['pageInfo']['total']} ***")
            response = make_api_request(graphql_query, variables, app)

            if response is not None:
                app.logger.debug('*** RESPONSE WORKED, EXTEND all_staff ***')
                search_staff = response['data']['Page']
                all_staff.extend(search_staff['staff'])
            else:
                break

        response_data = {
            "data": {
                "status_code": 200,
                "va": all_staff,
            }
        }
        return response_data

    # If the response is None, return a dictionary with a status_code key
    return {
        "data": {
            "status_code": response.status_code if response else 500,
            "va": [],
        }
    }

def fetch_all_character_media(va_id, app):
    """Fetch all characterMedia series for a VA based on ID."""

    # GraphQL query to fetch characterMedia by staff ID
    graphql_query = '''
    query ($id: Int, $page: Int, $perPage: Int) {
        Staff(id: $id) {
            characterMedia(page: $page, perPage: $perPage) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                }
                edges {
                    node {
                        id
                        idMal
                        title {
                            romaji
                            english
                            userPreferred
                        }
                        type
                        seasonYear
                        coverImage {
                            large
                            medium
                            color
                        }
                        averageScore
                        meanScore
                        popularity
                        trending
                        favourites
                    }
                    characters {
                        id
                        name {
                            full
                        }
                        image {
                            large
                            medium
                        }
                    }
                }
            }
        }
    }
    '''

    # Variables for the GraphQL query
    variables = {
        'id': va_id,
        'page': 1,
        'perPage': 25
    }

    # Make the initial API request
    response = make_api_request(graphql_query, variables, app)


    app.logger.debug(f'*** FETCH ALL CHARACTER MEDIA: {va_id} ***')

    if response is not None:
        app.logger.debug('***** RESPONSE IS NOT NONE *****')
        character_media = response['data']['Staff']['characterMedia']
        all_series = character_media['edges']

        # Fetch additional pages if available
        while character_media['pageInfo']['hasNextPage']:
            app.logger.debug("*** NEXT PAGE AVAIL, +1 PAGE AND REQUEST API AGAIN ***")
            variables['page'] += 1
            app.logger.debug(f"*** PAGE {variables['page']} OF {character_media['pageInfo']['total']} ***")
            response = make_api_request(graphql_query, variables, app)

            #print(f'@@@@ REQUESTED PAGE {variables['page']} OF {character_media['pageInfo']['total']} @@@@')

            if response is not None:

                app.logger.debug('*** RESPONSE WORKED, EXTEND all_series ***')
                character_media = response['data']['Staff']['characterMedia']
                #app.logger.debug('EXTENSION: ', character_media['edges'])
                all_series.extend(character_media['edges'])
            else:
                break

        #print('ALL SERIES FINAL: ', all_series)
        return all_series

    return []



def fetch_user_anime_list(username, app):
    """Fetch all completed / current by username"""

    # GraphQL query to fetch characterMedia by staff ID
    graphql_query = '''
    query UserListSearch($userName: String) {
        MediaListCollection(userName: $userName, type: ANIME, status_in: [COMPLETED, CURRENT]) {
            lists {
                name
                entries {
                    mediaId
                    status
                    score
                }
            }
        }
    }
    '''

    # Variables for the GraphQL query
    variables = {
        "userName": username
    }

    # Make the initial API request
    response = make_api_request(graphql_query, variables, app)

    all_series = {}

    if response is not None:
        app.logger.debug('*** USER LIST RESPONSE: IS NOT NONE ***')
        lists = response['data']['MediaListCollection']['lists']

        # Combine all entries from all lists
        for lst in lists:
            app.logger.debug(f"{lst['name']} Length: {len(lst['entries'])}")
            for entry in lst['entries']:
                all_series[entry['mediaId']] = {
                    'status': entry['status'],
                    'score': entry['score']
                }
                #all_series.append(entry['mediaId'])

        app.logger.debug(f'ALL_SERIES: {len(all_series)}')
        # print('ENTRIES: ', len(lists[-1]['entries']))

    #print(all_series)
    return all_series

def is_anilist_username_accessible(username, app):
    """Check if the AniList username is accessible."""

    # GraphQL query to fetch user profile by username
    graphql_query = '''
    query ($name: String) {
        User(name: $name) {
            id
            name
        }
    }
    '''

    # Variables for the GraphQL query
    variables = {
        "name": username
    }

    # Make the initial API request
    response = make_api_request(graphql_query, variables, app)

    # Check if the request returned an error
    if 'errors' in response and response['errors'][0]['status'] == 404:
        app.logger.debug('The username does not exist on Anilist or the profile is private.')
        #flash('The username does not exist on Anilist or the profile is private.', 'error')
        return False

    # If there was no error, the username is accessible
    return True


def search_anime_series(search_query, app):
    """Fetch all media based on search query"""

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
            media(search: $search, type: ANIME) {
                id
                idMal
                title {
                    romaji
                    english
                }
                seasonYear
                season
                averageScore
                popularity
                type
                format
                coverImage {
                    extraLarge
                    large
                    medium
                    color
                }
                description
            }
        }
    }
    '''

    # Variables for the GraphQL query
    variables = {
        'search': search_query,
        'page': 1,
        'perPage': 50
    }

    # Make the initial API request
    response = make_api_request(graphql_query, variables, app)

    app.logger.debug(f'*** SEARCH SERIES: {search_query} ***')

    if response is not None:
        app.logger.debug('***** RESPONSE IS NOT NONE *****')
        search_media = response['data']['Page']
        all_media = search_media['media']

        # Fetch additional pages if available
        while search_media['pageInfo']['hasNextPage']:
            app.logger.debug("*** NEXT PAGE AVAIL, +1 PAGE AND REQUEST API AGAIN ***")
            variables['page'] += 1
            app.logger.debug(f"*** PAGE {variables['page']} OF {search_media['pageInfo']['total']} ***")
            response = make_api_request(graphql_query, variables, app)

            #print(f'@@@@ REQUESTED PAGE {variables['page']} OF {search_media['pageInfo']['total']} @@@@')

            if response is not None:
                app.logger.debug('*** RESPONSE WORKED, EXTEND all_media ***')
                search_media = response['data']['Page']
                #app.logger.debug('EXTENSION: ', search_media['media'])
                all_media.extend(search_media['media'])
            else:
                break

        #print('ALL SERIES FINAL: ', all_media)
        response_data = {
            "data": {
                "status_code": 200,
                "series": all_media,
            }
        }
        return response_data

    # If the response is None, return a dictionary with a status_code key
    return {
        "data": {
            "status_code": response.status_code if response else 500,
            "series": [],
        }
    }
    # Response is none, return empty and 400 code
    # return {"status_code": 404, "all_media": []}


def fetch_series_characters_roles(series_id, app):
    """Fetch all characters and their VA's for a series based on ID."""

    # Reworked query not pulling extra media on voiceActor > characters query
    graphql_query2 = '''
    query ($id: Int, $page: Int, $perPage: Int) {
        Media(id: $id) {
            characters (page: $page, perPage: $perPage, sort: FAVOURITES_DESC) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                }
                edges {
                    role
                    node {
                        id
                        name {
                            full
                        }
                        image {
                            large
                            medium
                        }
                    }
                    voiceActors (language: JAPANESE) {
                        name {
                            full
                        }
                        id
                        image {
                            large
                            medium
                        }
                        characters (page: 1, perPage: 6, sort:FAVOURITES_DESC) {
                            nodes {
                                name {
                                    full
                                }
                                id
                                image {
                                    large
                                    medium
                                }
                            }
                        }
                    }
                }
            }
		}
    }
    '''

    # GraphQL query to fetch characterMedia by staff ID
    graphql_query = '''
    query ($id: Int, $page: Int, $perPage: Int) {
        Media(id: $id) {
            characters (page: $page, perPage: $perPage, sort: FAVOURITES_DESC) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                }
                edges {
                    node {
                        id
                        name {
                            full
                        }
                        image {
                            large
                            medium
                        }
                    }
                    voiceActors (language: JAPANESE) {
                        name {
                            full
                        }
                        id
                        image {
                            large
                            medium
                        }
                        characters (page: 1, perPage: 5, sort:FAVOURITES_DESC) {
                            nodes {
                                name {
                                    full
                                }
                                id
                                image {
                                    large
                                    medium
                                }
                                media {
                                    edges {
                                        node {
                                            id
                                            title {
                                                english
                                                romaji
                                            }
                                            type
                                            favourites
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
		}
    }
    '''

    # Variables for the GraphQL query
    variables = {
        'id': series_id,
        'page': 1,
        'perPage': 25
    }

    # Make the initial API request
    response = make_api_request(graphql_query2, variables, app)


    app.logger.debug(f'*** FETCH ALL SERIES CHARACTERS: {series_id} ***')

    if response is not None:
        app.logger.debug('***** RESPONSE IS NOT NONE *****')
        series_media = response['data']['Media']['characters']
        all_series = series_media['edges']

        # Fetch additional pages if available
        while series_media['pageInfo']['hasNextPage']:
            app.logger.debug("*** NEXT PAGE AVAIL, +1 PAGE AND REQUEST API AGAIN ***")
            variables['page'] += 1
            app.logger.debug(f"*** PAGE {variables['page']} OF {series_media['pageInfo']['total']} ***")
            response = make_api_request(graphql_query, variables, app)

            #print(f'@@@@ REQUESTED PAGE {variables['page']} OF {series_media['pageInfo']['total']} @@@@')

            if response is not None:

                app.logger.debug('*** RESPONSE WORKED, EXTEND all_series ***')
                series_media = response['data']['Media']['characters']
                #app.logger.debug('EXTENSION: ', series_media['edges'])
                all_series.extend(series_media['edges'])
            else:
                break

        #print('ALL SERIES FINAL: ', all_series)
        return all_series

    return []