
import streamlit as st
from main import new_df, recommend

st.set_page_config(
    page_title="CineMatch | Movie Recommendation",
    page_icon="🎬",
    layout="wide"
)

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
    background-color: #20202b;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    min-height: 70px;
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
</style>
""", unsafe_allow_html=True)

# HEADER
st.title("🎬 CINEMATCH")

st.markdown(
    "<h3 style='text-align:center;'>Discover Your Next Favourite Movie</h3>",
    unsafe_allow_html=True
)

st.write("---")

# MOVIE SELECTION
movie_list = sorted(new_df['title'].dropna().unique())

selected_movie = st.selectbox(
    "🍿 Select Your Favourite Movie",
    movie_list
)

# RECOMMENDATION BUTTON
if st.button("✨ Recommend Movies"):

    recommendations = recommend(selected_movie)

    st.markdown(f"## Movies Similar to {selected_movie}")

    if recommendations:

        cols = st.columns(5)

        for i, movie in enumerate(recommendations):

            movie_data = new_df[
                new_df['title'] == movie
            ].iloc[0]

            with cols[i]:

                st.markdown(
                    f"""
                    <div class="movie-card">
                        <h4>{movie}</h4>
                        <p>⭐ Rating: {movie_data['vote_average']}</p>
                        <p>📅 Release Date: {movie_data['release_date']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    else:
        st.warning("No recommendations found.")

