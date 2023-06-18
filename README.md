# Onsei - Anime Voice Actor Search App

Onsei is a voice actor discovery application built using Python, Flask, GraphQL, WTForms, Jinja2, SQLAlchemy, JavaScript & jQuery.

Onsei enables users to delve into anime series and identify the voice actors behind their favourite characters, as well as offering the option to directly search for specific voice actors to view the variety of characters they've voiced across different series.

Furthermore, users can integrate their AniList.co account with Onsei. This feature allows the sorting and filtering of Voice Actor results to focus specifically on the anime series they've watched, leveraging the data from their AniList anime list.

## Features

-   **Series Search**: Users can search for an anime series, then explore the characters and associated voice actor. With quick access to see that voice actor's most popular roles.
-   **Voice Actor Search**: Users can view detailed information about a voice actor, view every chatacter (and associated series) they've portrayed, and can sort / filter the results to their own watched series via their AniList.co username.
-   **User Authentication**: User registration and authentication system is implemented using Flask's user management features.

### Series Lookup

![Onsei Series Page](https://github.com/jassibacha/onsei/blob/main/static/images/screens/series-details.png?raw=true)

### Voice Actor Lookup

![Onsei VA Page](https://github.com/jassibacha/onsei/blob/main/static/images/screens/va-details.png?raw=true)

## Technologies

-   Python 3.7
-   GraphQL API
-   Javascript ES6
-   Bootstrap 5
-   JQuery 3
-   FontAwesome 6
-   Axios

## Deployment

Onsei is deployed using [Render](https://render.com) and the db is hosted on [ElephantSQL](https://www.elephantsql.com/). The app is accessible at [Onsei](https://onsei.onrender.com/).

## Installation

To run the Onsei app locally, follow these steps:

1. Clone the repository:

  <pre>
  git clone https://github.com/jassibacha/onsei
  cd Onsei
  </pre>

2. Create and activate a virtual environment:

  <pre>
  python3 -m venv venv
  source venv/bin/activate
  </pre>

3. Install the required dependencies:

    <pre>
    pip install -r requirements.txt
    </pre>

4. Set up Environment Variables

To set up the environment variables, follow these steps:

1. Create a .env file in the root directory of the project.

2. Add the following variables to the file with appropriate values:


    <pre>
    SECRET_KEY=your_secret_key
    DATABASE_URL=your_database_url
    </pre>

5.  Run the Flask development server:

    <pre>
    flask run
    </pre>

    The app will be accessible at http://localhost:5000 or http://127.0.0.1:5000

## Database Setup

### Onsei uses a PostgreSQL database hosted on ElephantSQL. To set up the database:

-   Create a PostgreSQL database locally, or on ElephantSQL or equivalent.

-   Update the DATABASE_URL variable with the connection URL for your database.

-   Run the database migration to create the necessary tables:

    <pre>
    flask db init
    flask db migrate --message 'Initial migration'
    flask db upgrade
    </pre>

    This will create the required tables in the database.

## Contributing

Contributions to Onsei are more than welcome! The goal with this is to build it out to support multiple anime tracking services (MyAnimeList, Kitsu, etc.)

If you manage to find any bugs or have suggestions for new features, please open an issue or submit a pull request. We may be launching a Discord soon depending on interest.

\*\* Make sure to follow the existing code style and conventions.

## License

This project is not licensed.
