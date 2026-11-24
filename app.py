import ast
import html
import streamlit as st
import requests
import os
from dotenv import load_dotenv
from main import new_df, recommend

load_dotenv()

API_KEY = st.secrets["TMDB_API_KEY"]

st.set_page_config(
    page_title="CineMatch | Movie Recommendation",
    page_icon="🎬",
    layout="wide"
)

if not API_KEY:
    st.error("TMDB API Key not found. Check your .env file.")
    st.stop()


# FETCH MOVIE POSTER

@st.cache_data(ttl=3600)
def fetch_poster(movie_title):

    url = "https://api.themoviedb.org/3/search/movie"

    params = {
        "api_key": API_KEY,
        "query": movie_title
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        if data.get("results"):
            poster_path = data["results"][0].get("poster_path")

            if poster_path:
                return "https://image.tmdb.org/t/p/w500" + poster_path

        return None

    except requests.exceptions.RequestException:
        return None


# FETCH MOVIE DETAILS

@st.cache_data(ttl=3600)
def fetch_movie_details(movie_title):

    search_url = "https://api.themoviedb.org/3/search/movie"

    params = {
        "api_key": API_KEY,
        "query": movie_title
    }

    try:
        response = requests.get(
            search_url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        results = response.json().get("results", [])

        if not results:
            return None

        movie_id = results[0]["id"]

        details_url = f"https://api.themoviedb.org/3/movie/{movie_id}"

        details_params = {
            "api_key": API_KEY
        }

        details_response = requests.get(
            details_url,
            params=details_params,
            timeout=20
        )

        details_response.raise_for_status()

        return details_response.json()

    except requests.exceptions.RequestException:
        return None
    # FETCH BETTER RECOMMENDATIONS FROM TMDB
@st.cache_data(ttl=3600)
def fetch_tmdb_recommendations(movie_id, source_language="hi", source_genre_ids=None):
    """Fetch recommendations and rank them by language, genre and rating quality."""
    endpoints = [
        f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations",
        f"https://api.themoviedb.org/3/movie/{movie_id}/similar"
    ]

    source_genre_ids = set(source_genre_ids or [])
    collected = {}

    for url in endpoints:
        params = {
            "api_key": API_KEY,
            "language": "en-US",
            "page": 1
        }

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()

            for movie in response.json().get("results", []):
                result_id = movie.get("id")
                rating = float(movie.get("vote_average") or 0)
                vote_count = int(movie.get("vote_count") or 0)
                language = movie.get("original_language")

                # Keep the same language and remove weak/poorly-rated results.
                if language != source_language:
                    continue
                if rating < 5.0 or vote_count < 20:
                    continue
                if not result_id:
                    continue

                movie_genres = set(movie.get("genre_ids") or [])
                genre_matches = len(source_genre_ids.intersection(movie_genres))
                movie["_genre_matches"] = genre_matches
                collected[result_id] = movie

        except requests.exceptions.RequestException:
            continue

    results = list(collected.values())

    # Prefer movies sharing one or more genres with the searched movie.
    genre_matched = [movie for movie in results if movie["_genre_matches"] > 0]
    if genre_matched:
        results = genre_matched

    # Sort by genre overlap first, then rating and number of votes.
    results.sort(
        key=lambda movie: (
            movie.get("_genre_matches", 0),
            movie.get("vote_average", 0),
            movie.get("vote_count", 0)
        ),
        reverse=True
    )

    for movie in results:
        movie.pop("_genre_matches", None)

    return results[:10]


# CUSTOM CSS

st.markdown("""
<style>

.stApp {
    background-color: #101018;
    color: white;
}

h1 {
    color: #E50914;
    text-align: center;
}

.movie-card {
    background: linear-gradient(145deg, #29293b, #171720);
    padding: 15px;
    border-radius: 0 0 14px 14px;
    text-align: left;
    min-height: 245px;
    border: 1px solid #383848;
    border-top: 0;
    box-shadow: 0 6px 16px rgba(0,0,0,0.28);
    margin-top: -8px;
}

[data-testid="stImage"] img {
    border-radius: 14px 14px 0 0;
    object-fit: cover;
}

.movie-card h4 {
    color: #ffffff;
    font-size: 17px;
    line-height: 1.35;
    min-height: 44px;
    margin: 2px 0 10px 0;
}

.movie-meta {
    color: #dddddf;
    font-size: 12px;
    margin: 5px 0;
}

.genre-tag {
    display: inline-block;
    background: #3a2530;
    color: #ffb7c0;
    border: 1px solid #74303d;
    border-radius: 20px;
    padding: 4px 8px;
    margin: 3px 3px 5px 0;
    font-size: 10px;
}

.movie-overview {
    color: #c8c8d0;
    font-size: 12px;
    line-height: 1.5;
    margin-top: 9px;
}

.stButton > button {
    background-color: #E50914;
    color: white;
    border-radius: 8px;
    border: none;
    width: 100%;
    font-weight: bold;
}

.stButton > button:hover {
    background-color: #b20710;
    color: white;
}

/* MOVIE DETAILS EXPANDER */

[data-testid="stExpander"] details {
    background-color: #20202b !important;
    border: 1px solid #444 !important;
    border-radius: 10px !important;
}

[data-testid="stExpander"] summary {
    background-color: #20202b !important;
    color: white !important;
}

[data-testid="stExpander"] summary p {
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown("""
<div style="
    background: linear-gradient(135deg, #20202b, #3b1018);
    padding: 35px;
    border-radius: 15px;
    text-align: center;
    margin-bottom: 25px;
">
    <h1 style="color: #E50914; font-size: 45px;">
        🎬 CINEMATCH
    </h1>
    <h3 style="color: white;">
        Discover Your Next Favourite Movie
    </h3>
    <p style="color: #cccccc; font-size: 17px;">
        Find movies you love with our intelligent
        movie recommendation system.
    </p>
    <p style="color: #E50914; font-weight: bold;">
        Search • Discover • Enjoy
    </p>
</div>
""", unsafe_allow_html=True)

st.write("---")


# GENRE FILTER

def get_genres(genre_data):
    try:
        if isinstance(genre_data, str):
            genres = ast.literal_eval(genre_data)
        elif isinstance(genre_data, list):
            genres = genre_data
        else:
            return []

        if all(isinstance(genre, str) for genre in genres):
            return genres

        return [
            genre["name"]
            for genre in genres
            if isinstance(genre, dict) and "name" in genre
        ]

    except (ValueError, TypeError, SyntaxError):
        return []


# TMDB genre IDs used by recommendation results
TMDB_GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
}


def render_movie_card(poster_url, title, rating, release_date, genres=None, overview=""):
    """Display a consistent poster and information card."""
    if poster_url:
        st.image(poster_url, use_container_width=True)
    else:
        st.markdown(
            "<div style='background:#252535;border-radius:14px;padding:70px 8px;text-align:center;'>🎬<br>Poster not available</div>",
            unsafe_allow_html=True
        )

    safe_title = html.escape(str(title or "Unknown"))
    safe_rating = html.escape(str(rating if rating is not None else "N/A"))
    safe_date = html.escape(str(release_date or "Not available"))
    genre_html = "".join(
        f"<span class='genre-tag'>{html.escape(str(genre))}</span>"
        for genre in (genres or []) if genre
    )
    safe_overview = html.escape(str(overview or "Overview not available."))
    if len(safe_overview) > 185:
        safe_overview = safe_overview[:182] + "..."

    st.markdown(
        f"""
        <div class="movie-card">
            <h4>{safe_title}</h4>
            <div class="movie-meta">⭐ <b>{safe_rating}</b> &nbsp; | &nbsp; 📅 {safe_date}</div>
            <div>{genre_html or '<span class="genre-tag">Movie</span>'}</div>
            <div class="movie-overview">{safe_overview}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


all_genres = [
    "Action", "Adventure", "Animation", "Comedy",
    "Crime", "Documentary", "Drama", "Family",
    "Fantasy", "History", "Horror", "Music",
    "Mystery", "Romance", "Science Fiction",
    "TV Movie", "Thriller", "War", "Western"
]

st.markdown("## 🎭 Explore Movies by Genre")

selected_genre = st.selectbox(
    "Select Movie Genre",
    ["All Genres"] + all_genres
)

if selected_genre == "All Genres":
    genre_df = new_df
else:
    genre_df = new_df[
        new_df["genres"].apply(
            lambda value: selected_genre in get_genres(value)
        )
    ]

# MOVIE SEARCH

movie_list = sorted(genre_df["title"].dropna().unique())

search_movie = st.text_input(
    "🔍 Search Your Favourite Movie",
    placeholder="Enter movie name..."
)

if search_movie:
    filtered_movies = [
        movie for movie in movie_list
        if search_movie.lower() in movie.lower()
    ]
else:
    filtered_movies = movie_list

if filtered_movies:
    selected_movie = st.selectbox(
        "🍿 Select Your Favourite Movie",
        filtered_movies
    )
else:
    selected_movie = None
    st.warning("Movie not found in our recommendation dataset.")

    if search_movie.strip():
        if st.button("🔍 Search on TMDB"):
            tmdb_movie = fetch_movie_details(search_movie.strip())

            if tmdb_movie:
                st.markdown("### 🎬 Movie Found on TMDB")

                col1, col2 = st.columns([1, 2])

                with col1:
                    poster_path = tmdb_movie.get("poster_path")

                    if poster_path:
                        st.image(
                            "https://image.tmdb.org/t/p/w500" + poster_path,
                            use_container_width=True
                        )
                    else:
                        st.write("🎬 Poster not available")

                with col2:
                    st.subheader(tmdb_movie.get("title", "Unknown"))
                    st.write("⭐ Rating:", tmdb_movie.get("vote_average", "N/A"))
                    st.write("📅 Release Date:", tmdb_movie.get("release_date") or "N/A")
                    st.write("**Description:**")
                    st.write(tmdb_movie.get("overview") or "Description not available.")

                # SHOW SIMILAR MOVIES FROM TMDB
                st.markdown(f"## 🎥 Movies Similar to {tmdb_movie.get('title', search_movie)}")

                source_language = tmdb_movie.get("original_language", "hi")
                source_genre_ids = [
                    genre.get("id") for genre in tmdb_movie.get("genres", [])
                    if genre.get("id") is not None
                ]
                similar_movies = fetch_tmdb_recommendations(
                    tmdb_movie["id"], source_language, source_genre_ids
                )

                if similar_movies:
                    cols = st.columns(5)

                    for i, movie in enumerate(similar_movies):
                        with cols[i % 5]:
                            poster_path = movie.get("poster_path")
                            poster_url = (
                                "https://image.tmdb.org/t/p/w500" + poster_path
                                if poster_path else None
                            )
                            movie_genres = [
                                TMDB_GENRES.get(genre_id, "")
                                for genre_id in movie.get("genre_ids", [])
                            ]
                            render_movie_card(
                                poster_url=poster_url,
                                title=movie.get("title"),
                                rating=movie.get("vote_average"),
                                release_date=movie.get("release_date"),
                                genres=movie_genres,
                                overview=movie.get("overview")
                            )
                else:
                    st.info(
                        "No relevant movies were found in the same language. "
                        "Try another movie title."
                    )

            else:
                st.error("Movie not found on TMDB either.")

# TOP RATED MOVIES

if st.button("⭐ Show Top Rated Movies"):

    top_movies = (
        new_df.sort_values(
            by="vote_average",
            ascending=False
        )
        .drop_duplicates(subset="title")
        .head(5)
    )

    st.markdown("## ⭐ Top 5 Highest Rated Movies")

    cols = st.columns(5)

    for i, (_, movie_data) in enumerate(top_movies.iterrows()):

        with cols[i]:

            poster = fetch_poster(movie_data["title"])

            render_movie_card(
                poster_url=poster,
                title=movie_data["title"],
                rating=movie_data.get("vote_average", "N/A"),
                release_date=movie_data.get("release_date", "Not available"),
                genres=get_genres(movie_data.get("genres", [])),
                overview="Discover this top-rated movie in CineMatch."
            )


# RECOMMENDATION BUTTON

if st.button("✨ Recommend Movies", disabled=not selected_movie):

    recommendations = recommend(selected_movie)

    st.markdown(f"## Movies Similar to {selected_movie}")

    if recommendations:

        cols = st.columns(5)

        for i, movie in enumerate(recommendations):

            movie_data = new_df[
                new_df["title"] == movie
            ].iloc[0]

            details = fetch_movie_details(movie)

            with cols[i % 5]:

                poster = fetch_poster(movie)

                movie_genres = details.get("genres", []) if details else []
                movie_genres = [genre.get("name", "") for genre in movie_genres]
                render_movie_card(
                    poster_url=poster,
                    title=movie,
                    rating=movie_data.get("vote_average", "N/A"),
                    release_date=movie_data.get("release_date", "Not available"),
                    genres=movie_genres or get_genres(movie_data.get("genres", [])),
                    overview=details.get("overview", "") if details else ""
                )

                with st.expander("📖 More Movie Details"):

                    if details:

                        st.write("**Description:**")

                        st.write(
                            details.get(
                                "overview",
                                "Description not available."
                            ) or "Description not available."
                        )

                        genres = details.get("genres", [])

                        if genres:
                            genre_names = ", ".join(
                                genre["name"] for genre in genres
                            )
                            st.write("**Genre:**", genre_names)

                        runtime = details.get("runtime")

                        if runtime:
                            st.write(
                                "**Runtime:**",
                                f"{runtime} minutes"
                            )

                        st.write(
                            "**Release Date:**",
                            details.get("release_date") or "Not available"
                        )

                        st.write(
                            "**TMDB Rating:**",
                            details.get("vote_average", "Not available")
                        )

                    else:
                        st.write(
                            "Movie details are currently unavailable."
                        )

    else:
        st.warning("No recommendations found.")

