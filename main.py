import pandas as pd
import numpy as np
import ast
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

movies = pd.read_csv("dataset/tmdb_5000_movies.csv")
credits = pd.read_csv("dataset/tmdb_5000_credits.csv")

print("MOVIES DATASET")
print(movies.head())

print("\nCREDITS DATASET")
print(credits.head())

print("\nMovies Shape:", movies.shape)
print("Credits Shape:", credits.shape)

print("\nMovies Columns:")
print(movies.columns)

print("\nCredits Columns:")
print(credits.columns)

print("\nMISSING VALUES IN MOVIES")
print(movies.isnull().sum())

print("\nMISSING VALUES IN CREDITS")
print(credits.isnull().sum())

print("\nDUPLICATE MOVIES")
print(movies.duplicated().sum())

print("\nDUPLICATE CREDITS")
print(credits.duplicated().sum())

print("\nMOVIES INFORMATION")
movies.info()

print("\nCREDITS INFORMATION")
credits.info()

# DATA CLEANING

movies['overview'] = movies['overview'].fillna('')

movies['runtime'] = movies['runtime'].fillna(
    movies['runtime'].median()
)

print("\nMISSING VALUES AFTER CLEANING")
print(movies[['overview', 'runtime']].isnull().sum())


# MERGING MOVIES AND CREDITS DATASETS

new_df = movies.merge(
    credits[['movie_id', 'cast', 'crew']],
    left_on='id',
    right_on='movie_id',
    how='left'
)

new_df = new_df.drop(columns=['movie_id'])

print("\nMERGED DATASET")
print(new_df.head())

print("\nMERGED DATASET SHAPE")
print(new_df.shape)

print("\nMERGED DATASET COLUMNS")
print(new_df.columns)
def convert(text):
    return ast.literal_eval(text)

def get_names(obj):
    return [item['name'] for item in convert(obj)]

def get_cast(obj):
    cast_list = convert(obj)
    return [item['name'] for item in cast_list[:3]]

def get_director(obj):
    crew_list = convert(obj)
    for item in crew_list:
        if item['job'] == 'Director':
            return item['name']
    return ''

new_df['genres'] = new_df['genres'].apply(get_names)
new_df['keywords'] = new_df['keywords'].apply(get_names)
new_df['cast'] = new_df['cast'].apply(get_cast)
new_df['crew'] = new_df['crew'].apply(get_director)

print("\nEXTRACTED MOVIE FEATURES")
print(new_df[['title', 'genres', 'keywords', 'cast', 'crew']].head())
new_df['overview'] = new_df['overview'].apply(
    lambda x: x.split()
)

print("\nEXTRACTED OVERVIEW")
print(new_df['overview'].head())
new_df['tags'] = (
    new_df['overview'] +
    new_df['genres'] +
    new_df['keywords'] +
    new_df['cast'] +
    new_df['crew'].apply(lambda x: [x])
)

print("\nCOMBINED MOVIE TAGS")
print(new_df[['title', 'tags']].head())
new_df['tags'] = new_df['tags'].apply(
    lambda x: " ".join(x)
)

new_df['tags'] = new_df['tags'].apply(
    lambda x: x.lower()
)

print("\nFINAL CLEANED TAGS")
print(new_df[['title', 'tags']].head())

# STAGE 6 - COUNT VECTORIZER

cv = CountVectorizer(max_features=5000, stop_words='english')

vectors = cv.fit_transform(new_df['tags']).toarray()

print("\nVECTOR SHAPE:")
print(vectors.shape)
# STAGE 7 - COSINE SIMILARITY

similarity = cosine_similarity(vectors)

print("\nSIMILARITY MATRIX SHAPE:")
print(similarity.shape)


# STAGE 8 - MOVIE RECOMMENDATION FUNCTION

def recommend(movie):

    if movie not in new_df['title'].values:
        return []

    movie_index = new_df[new_df['title'] == movie].index[0]

    distances = similarity[movie_index]

    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    recommended_movies = []

    for i in movies_list:
        recommended_movies.append(new_df.iloc[i[0]].title)

    return recommended_movies
print(new_df.columns.tolist())
