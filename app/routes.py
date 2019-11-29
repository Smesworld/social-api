from app import app, db
from app.models import User, Genre, User_genre, Movie, Later_movie, Favorited_movie
from flask import request, make_response, jsonify
from flask_cors import CORS
import requests
import json
import random
from flask import request
import dotenv
import os

dotenv.load_dotenv()
TMDB_key = os.getenv('TMDB_KEY')

CORS(app)

@app.route("/suggestion", methods=['GET', 'POST'])
def suggestions():
  req = json.loads(request.data)
  min_runtime = req['minimumRuntime']
  max_runtime = req['maximumRuntime']
  print(min_runtime)
  print(max_runtime)


  suggested_ids = []
  for suggestion in req['recentSuggestions']:
    suggested_ids.append(suggestion['newSuggestion']['tmdb_id'])
  
  user_genre_preferences = req['userGenrePreferences']

  # Confert user preferences to more useable object
  preferences = {}
  for user_preference in user_genre_preferences:
    preferences[user_preference['id']] = user_preference['preference']

  # Get any group preferences
  for user in req['group']:
    genre_preferences = User_genre.query.filter(User_genre.user_id == user['friend']['id']).all()

    for genre in genre_preferences:
      if preferences[genre.genre.genre_api_id] != False:
        if genre.preference == False:
          preferences[genre.genre.genre_api_id] = False
        elif genre.preference == True:
          preferences[genre.genre.genre_api_id] = True

  # Do some things to the lists to make them in a thing
  user_loved_genres = []
  user_meh_genres = []
  user_hated_genres = []

  for genre in preferences:
    if preferences[genre] == True:
      user_loved_genres.append(str(genre))
    elif preferences[genre] == "" or preferences[genre] == None:
      user_meh_genres.append(str(genre))
    elif preferences[genre] == False:
      user_hated_genres.append(str(genre))

  if len(user_meh_genres) == 0 and len(user_loved_genres) == 0:
    full_hate_info = {
      "title": "No Movie For You",
      "description": "It seems you are not the moving watching kind",
    }
  
    full_hate_info = {
    "title": "Bob Ross: The Happy Painter",
    "poster": "https://image.tmdb.org/t/p/w500/yhV6rSv8Ry80lyDL8sjZpu8hzph.jpg",
    "description": "We couldn't find an appropriate movie to recommend based on the current genre prefernces. However, we believe everyone will enjoy this!",
    "release_date": "2011-12-03",
    "tmdb_id": "238959",
    "imdb_link": "https://www.imdb.com/title/tt2155259/"
    }

    full_hate_info_json = json.dumps(full_hate_info)
    return full_hate_info_json

  if len(user_hated_genres) > 1:
    hated_list = (",".join(user_hated_genres))
  elif len(user_hated_genres) == 1:
    hated_list = user_hated_genres[0]
  elif len(user_hated_genres) == 0:
    hated_list = "0"

  user_loved_genres_loop_copy = user_loved_genres.copy()
  user_meh_genres_loop_copy = user_meh_genres.copy()
  all_results = []

  while len(all_results) == 0:
    page_num = random.randint(1, 3)

    if len(user_loved_genres_loop_copy) != 0:
      index = random.randint(0, (len(user_loved_genres_loop_copy) - 1))
      r = requests.get("https://api.themoviedb.org/3/discover/movie?api_key={}&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page={}&with_genres={}&without_genres={}&with_runtime.gte={}&with_runtime.lte={}".format(TMDB_key, page_num, user_loved_genres[index], hated_list, min_runtime, max_runtime))
      del user_loved_genres_loop_copy[index]
    elif len(user_meh_genres_loop_copy) != 0:
      index = random.randint(0, (len(user_meh_genres_loop_copy) - 1))
      r = requests.get("https://api.themoviedb.org/3/discover/movie?api_key={}&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page={}&with_genres={}&without_genres={}&with_runtime.gte={}&with_runtime.lte={}".format(TMDB_key, page_num, user_meh_genres[index], hated_list, min_runtime, max_runtime))
      del user_meh_genres_loop_copy[index]
    else:
      index = 0
      r = requests.get("https://api.themoviedb.org/3/discover/movie?api_key={}&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page={}&with_genres={}&without_genres={}&with_runtime.gte={}&with_runtime.lte={}".format(TMDB_key, page_num, user_meh_genres[index], hated_list, min_runtime, max_runtime))


    tmdb_result = json.loads(r.text)
    results = tmdb_result["results"]
    
    for index, result in enumerate(results):
      # print('result: ', result['id'])
      # print('index: ', index)
      if result['id'] in suggested_ids:
        print("it was in here!")
        print(result['title'])
        del results[index]
        
    all_results += results

  selected_result = all_results[(random.randint(0, (len(all_results) - 1)))]

  details_r = requests.get("https://api.themoviedb.org/3/movie/{}?api_key={}&language=en-US".format(selected_result["id"], TMDB_key))
  detailed_result = json.loads(details_r.text)
  imdb_id = detailed_result["imdb_id"]
  runtime = detailed_result["runtime"]
  if selected_result["poster_path"]:
    poster = "https://image.tmdb.org/t/p/w500" + selected_result["poster_path"]
  else:
    poster = ""

  if imdb_id:
    imdb_link = "https://www.imdb.com/title/{}/".format(imdb_id)
  else:
    imdb_link = "https://www.imdb.com/"

  movie_info = {
    "title": selected_result["title"],
    "poster": poster,
    "description": selected_result["overview"],
    "release_date": selected_result["release_date"],
    "tmdb_id": selected_result["id"],
    "imdb_link": imdb_link,
    "runtime" : runtime
  }

  movie_info_json = json.dumps(movie_info)
  return movie_info_json

@app.route("/hello")
def hello():
  u = User.query.all()[0]
  return "Hello World! {}".format(u.name)

@app.route("/api/users")
def users():
  users = User.query.all()
  user_list = []
  for user in users:
    user_list.append({"id":user.id, "name":user.name, "icon":user.icon})
  
  res = {
    "users": user_list
  }
  res_json = json.dumps(res)

  return res_json

@app.route("/api/genres")
def genres():
  genres = Genre.query.all()
  genre_arr = []
  for genre in genres:
    genre_arr.append({"id": genre.genre_api_id, "name": genre.genre_name})

  genres_json = json.dumps(genre_arr)
  return make_response(jsonify(genre_arr)), 200

@app.route("/api/<user>/genres", methods=['GET', 'POST'])
def userGenres(user):
  user = User.query.filter(User.name == user).one_or_none()

  if request.method == 'POST':
    req = json.loads(request.data)

    genre = Genre.query.filter(Genre.genre_api_id == req['id']).first()

    update_genre = User_genre.query.filter(User_genre.user_id == user.id, User_genre.genre_id == genre.id).first()

    if not update_genre:
      update_genre = User_genre(user_id = user.id, genre_id = genre.id)

    if req['preference'] == "":
      update_genre.preference = None
    else:
      update_genre.preference = req['preference']

    db.session.add(update_genre)
    db.session.commit()

  genres = []

  for genre in user.user_genres:
    genres.append(
      {
        "id": genre.genre.genre_api_id,
        "preference": genre.preference
      }
    )

  res = {
    "genres": genres
  }

  res_json = json.dumps(res)

  return res_json

@app.route("/api/<user>/favmovies", methods=['GET', 'POST', 'DELETE'])
def userFavmovies(user):
  dbUser = User.query.filter(User.name == user).one_or_none()
  userFavMovies = dbUser.favorited_movies

  if request.method == 'POST':
    req = json.loads(request.data)
    title = req['movie']['title']
    image = req['movie']['poster']
    movie_api_id = req['movie']['tmdbId']

    
    
    new_movie = Movie.query.filter(Movie.movie_api_id == str(movie_api_id)).first()

    if new_movie == None:
      new_movie = Movie(title = title, movie_api_id = movie_api_id, image = image)    
      db.session.add(new_movie)
      db.session.commit()
      
    new_fave_movie = Favorited_movie(user_id = dbUser.id, movie_id = new_movie.id)
    db.session.add(new_fave_movie)
    db.session.commit()

  if request.method == 'DELETE':
    req = json.loads(request.data)

    remove_movie = Favorited_movie.query.filter(Favorited_movie.movie_id == req['id']).first()

    db.session.delete(remove_movie)
    db.session.commit()

  favorited_movies = []

  
  for fave_movie in dbUser.favorited_movies:
    favorited_movies.append(
      {
        "id": fave_movie.movie.id,
        "title": fave_movie.movie.title,
        "img": fave_movie.movie.image
      }
    )

  res = {
    "favorited_movies": favorited_movies
  }

  res_json = json.dumps(res)

  return res_json

@app.route("/api/<user>/latermovies", methods=['GET', 'POST', 'DELETE'])
def userLatemovies(user):

  dbUser = User.query.filter(User.name == user).one_or_none()
  userLaterMovies = dbUser.later_movies

  if request.method == 'POST':
    req = json.loads(request.data)

    title = req['suggestedMovie']['title']
    image = req['suggestedMovie']['poster']
    movie_api_id = req['suggestedMovie']['tmdbId']

    new_movie = Movie.query.filter(Movie.movie_api_id == str(movie_api_id)).first()

    if new_movie == None:
      new_movie = Movie(title = title, movie_api_id = movie_api_id, image = image)    
      db.session.add(new_movie)
      db.session.commit()

    new_later_movie = Later_movie(user_id = dbUser.id, movie_id = new_movie.id)
    db.session.add(new_later_movie)
    db.session.commit()

  if request.method == 'DELETE':
    req = json.loads(request.data)

    remove_movie = Later_movie.query.filter(Later_movie.movie_id == req['id']).first()

    db.session.delete(remove_movie)
    db.session.commit()

  later_movies = []
  for later_movie in dbUser.later_movies:
    later_movies.append(
      {
        "id": later_movie.movie.id,
        "title": later_movie.movie.title,
        "img": later_movie.movie.image
      }
    )

  res = {
    "later_movies": later_movies
  }

  res_json = json.dumps(res)

  return res_json

@app.route("/movies/title/")
def title():
  movie_title = request.args['title']
  movies = requests.get("https://api.themoviedb.org/3/search/movie?api_key={}&language=en-US&query={}&page=1&include_adult=false".format(TMDB_key, movie_title))
  movies_dict = movies.json()
  results = movies_dict["results"]

  movies = []

  for result in results: 
    result_title = result["title"]
    if result["poster_path"]:
      result_poster = "https://image.tmdb.org/t/p/w500" + result["poster_path"]
    else:
      result_poster = "Nope"
    result_description = result["overview"]
    result_release_date = result["release_date"]
    result_tmdb_id = result["id"]

    movie_info = {
      "title": result_title,
      "poster": result_poster,
      "description": result_description,
      "release_date": result_release_date,
      "tmdbId": result_tmdb_id
    }

    movies.append(movie_info)

    res = {
      "movies": movies
    }

  movies_json = json.dumps(res)

  return movies_json

@app.route("/signup", methods=['POST'])
def signup():
  req = json.loads(request.data)

  user = User.query.filter(User.name == req['name']).one_or_none()

  if user != None:
    return make_response(jsonify({ "error": "Username already exists." })), 401

  user = User(name=req['name'], icon="https://ui-avatars.com/api/?background=e3b04b&color=fff&size=50&rounded=true&bold=true&name={}".format(req['name']))
  user.set_password(req['password'])

  db.session.add(user)
  db.session.commit()

  for new_genre in req['genres']:
    genre = Genre.query.filter(Genre.genre_api_id == new_genre['id']).first()
    update_genre = User_genre(user_id = user.id, genre_id = genre.id)

    if new_genre['preference'] == "":
      update_genre.preference = None
    else:
      update_genre.preference = new_genre['preference']

    db.session.add(update_genre)

  db.session.commit()

  token = user.generate_token(user.id)

  user_info = {
    "id": user.id,
    "name": user.name,
    "avatar": user.icon,
    "token": token.decode()
  }

  res = {
    "user": user_info,
  }

  res_json = json.dumps(res)

  return res_json

@app.route("/login", methods=['GET', 'POST'])
def login():
  req = json.loads(request.data)

  user = User.query.filter(User.name == req['name']).one_or_none()
  print(user)
  if user == None or not user.check_password(req['password']):
    print("WE MADE IT")
    return make_response(jsonify({ "error": "Invalid password." })), 401

  genres = []

  for genre in user.user_genres:
    genres.append(
      {
        "id": genre.genre.genre_api_id,
        "preference": genre.preference
      }
    )

  userInfo = {
    "name": user.name,
    "avatar": user.icon
  }

  later_movies = []

  for later_movie in user.later_movies:
    later_movies.append(
      {
        "id": later_movie.movie.id,
        "title": later_movie.movie.title,
        "img": later_movie.movie.image
      }
    )
  favorited_movies = []

  for fave_movie in user.favorited_movies:
    favorited_movies.append(
      {
        "id": fave_movie.movie.id,
        "title": fave_movie.movie.title,
        "img": fave_movie.movie.image
      }
    )
  res = {
    "user": userInfo,
    "genres": genres,
    "later_movies": later_movies,
    "favorited_movies": favorited_movies
  }

  res_json = json.dumps(res)

  return res_json
