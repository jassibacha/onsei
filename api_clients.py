import requests
import json


def make_api_request(query, variables):

    # Set the GraphQL endpoint URL
    anilist_api_url = 'https://graphql.anilist.co'

    # Set the request headers
    anilist_api_headers = {'Content-Type': 'application/json'}

    response = requests.post(anilist_api_url, json={'query': query, 'variables': variables}, headers=anilist_api_headers)

    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print('Request failed with status code:', response.status_code)
        print('Response:', response.text)
        return None

def fetch_all_character_media(va_id):
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
    response = make_api_request(graphql_query, variables)

    if response is not None:
        print('*** RESPONSE IS NOT NONE ***')
        character_media = response['data']['Staff']['characterMedia']
        all_series = character_media['edges']

        # Fetch additional pages if available
        while character_media['pageInfo']['hasNextPage']:
            print('*** NEXT PAGE AVAIL, +1 PAGE AND REQUEST API AGAIN ***')
            variables['page'] += 1
            response = make_api_request(graphql_query, variables)

            #print(f'@@@@ REQUESTED PAGE {variables['page']} OF {character_media['pageInfo']['total']} @@@@')

            if response is not None:

                print('*** RESPONSE WORKED, EXTEND all_series ***')
                character_media = response['data']['Staff']['characterMedia']
                print('EXTENSION: ', character_media['edges'])
                all_series.extend(character_media['edges'])
            else:
                break

        #print('ALL SERIES FINAL: ', all_series)
        return all_series

    return []



def fetch_user_anime_list(username):
    """Fetch all characterMedia series for a VA based on ID."""

    # GraphQL query to fetch characterMedia by staff ID
    graphql_query = '''
    query UserListSearch($userName: String) {
        MediaListCollection(userName: $userName, type: ANIME, status_in: [COMPLETED, CURRENT]) {
            lists {
                name
                entries {
                    mediaId
                    status
                }
            }
        }
    }
    '''

    # Variables for the GraphQL query
    variables = {
        "userName": username,
        "chunk": 0,
        "perChunk": 500
    }

    # Make the initial API request
    response = make_api_request(graphql_query, variables)

    all_series = []

    while True:
        # Make the API request
        response = make_api_request(graphql_query, variables)

        if response is not None:
            print('*** USER LIST RESPONSE IS NOT NONE ***')
            lists = response['data']['MediaListCollection']['lists']

            # Combine all entries from all lists
            for list in lists:
                all_series.extend(list['entries'])

            # If the number of entries is less than perChunk, it means we've got all the data
            if len(lists[-1]['entries']) < variables['perChunk']:
                break

            # Otherwise, increase the chunk for the next iteration
            print('*** USER LIST +1 CHUNK ***')
            variables['chunk'] += 1

    print(all_series)

    return all_series