import requests

# Read the GraphQL query from a separate .txt file
with open('misc/anilist-graphql-query.txt', 'r') as f:
    query = f.read()

# Set the GraphQL endpoint URL
anilist_api_url = 'https://graphql.anilist.co'

# Set the request headers
headers = {'Content-Type': 'application/json'}

# Set the request data with the query
data = {'query': query}

# Send the POST request to the AniList GraphQL endpoint
response = requests.post(url, json=data, headers=headers)

# Process the response
if response.status_code == 200:
    result = response.json()
    print('******* WORKED *******')
    print(result)
    # Process the response data
else:
    print('Request failed with status code:', response.status_code)
