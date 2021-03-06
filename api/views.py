from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .forms import QueryForm, ReleaseForm, FilmSearchForm
from TwitterSearch import *
from tmdbv3api import TMDb, Discover, Movie
import pyrebase
import os
import json


def initializationDb():
    config = {
        "apiKey": os.environ['apiKey'],
        "authDomain": os.environ['authDomain'],
        "databaseURL": os.environ['databaseURL'],
        "storageBucket": os.environ['storageBucket']
    }
    firebase = pyrebase.initialize_app(config)
    email = os.environ['email']
    password = os.environ['password']
    # Get a reference to the auth service
    auth = firebase.auth()

    # Log the user in
    user = auth.sign_in_with_email_and_password(email, password)

    # Get a reference to the database service
    return firebase.database(), user['idToken'], user['localId']


@require_http_methods(["GET", "POST"])
def save(request):
    if request.method == 'GET':
        form = QueryForm()
        return render(request, 'save.html', {'form': form})
    elif request.method == 'POST':
        form = QueryForm(request.POST)
        if form.is_valid():
            try:
                db, token, uid = initializationDb()
                lang = request.POST.get("lang", "en")
                queryRaw = request.POST.get("query", "Film")
                count = int(request.POST.get("count", 10))
                query = queryRaw.split(';')
                tso = TwitterSearchOrder()
                tso.set_keywords(query)
                tso.set_include_entities(False)
                tso.set_count(count)
                if lang == 'en' or lang == 'id':
                    tso.set_language(lang)

                ts = TwitterSearch(
                    consumer_key=os.environ['consumerKey'],
                    consumer_secret=os.environ['consumerSecret'],
                    access_token=os.environ['accessToken'],
                    access_token_secret=os.environ['accessTokenSecret']
                )

                for tweet in ts.search_tweets_iterable(tso):
                    # Pass the user's idToken to the push method
                    data = {"username": tweet['user']['screen_name'], "tweet": tweet['text'],
                            "favorite_count": tweet['favorite_count'], "retweet_count": tweet['retweet_count'], "lang": lang}
                    db.child("uid").child("tweet").child(tweet['id']).set(data, token)
                response = {"status": 200, "message": "Success Save"}
                return JsonResponse(response)
            except TwitterSearchException as e:
                return HttpResponse(e)
        else:
            response = {"status": 401, "message": "Invalid Input"}
            return JsonResponse(response)


@require_http_methods(["GET", "POST"])
def movie_list(request):
    if request.method == 'GET':
        form = ReleaseForm()
        return render(request, 'movie_list.html', {'form': form})
    elif request.method == 'POST':
        form = ReleaseForm(request.POST)
        if form.is_valid():
            release_date_gte = request.POST.get('start', '2017-11-01')
            release_date_lte = request.POST.get('end', '2017-12-01')
            tmdb = TMDb()
            tmdb.api_key = os.environ['KEY-MDB']
            discover = Discover()
            movies = discover.discover_movies({
                'primary_release_date.gte': release_date_gte,
                'primary_release_date.lte': release_date_lte,
            })

            db, token, uid = initializationDb()
            for movie in movies:
                data = {"id": movie.id, "title": movie.title, "overview": movie.overview,
                        "poster_path": movie.poster_path, "release_date": movie.release_date, "popularity": movie.popularity,
                        "original_title": movie.original_title, "vote_count": movie.vote_count, "vote_average": movie.vote_average}
                db.child(uid).child("movie_list").child(movie.id).set(data, token)
            response = {"status": 200, "message": "Success Save"}
            return JsonResponse(response)
        else:
            response = {"status": 401, "message": "Invalid Input"}
            return JsonResponse(response)


@require_http_methods(["GET", "POST"])
def popular_movie(request):
    if request.method == 'GET':
        return render(request, 'search_popular.html')
    elif request.method == 'POST':
        tmdb = TMDb()
        tmdb.api_key = os.environ['KEY-MDB']
        movie = Movie()
        popular = movie.popular()

        db, token, uid = initializationDb()
        db.child("movie_popular").remove(token)
        for p in popular:
            data = {"id": p.id, "title": p.title, "overview": p.overview,
                    "poster_path": p.poster_path, "release_date": p.release_date, "popularity": p.popularity,
                    "original_title": p.original_title, "vote_count": p.vote_count, "vote_average": p.vote_average}
            db.child(uid).child("movie_popular").child(p.id).set(data, token)
        response = {"status": 200, "message": "Success Save"}
        return JsonResponse(response)


@require_http_methods(["GET", "POST"])
def search_movie(request):
    if request.method == 'GET':
        form = FilmSearchForm()
        return render(request, 'save_search.html', {'form': form})
    elif request.method == 'POST':
        form = FilmSearchForm(request.POST)
        if form.is_valid():
            tmdb = TMDb()
            tmdb.api_key = os.environ['KEY-MDB']
            movie = Movie()
            query = request.POST.get('query', 'Marlina')
            search = movie.search(query)

            db, token, uid = initializationDb()
            for p in search:
                data = {"id": p.id, "title": p.title,
                        "overview": p.overview, "poster_path": p.poster_path,
                        "release_date": p.release_date, "popularity": p.popularity,
                        "original_title": p.original_title, "vote_count": p.vote_count,
                        "vote_average": p.vote_average}
                db.child(uid).child("movie_list").child(p.id).set(data, token)
            response = {"status": 200, "message": "Success Save"}
            return JsonResponse(response)
        else:
            response = {"status": 401, "message": "Invalid Input"}
            return JsonResponse(response)


@require_http_methods(["GET"])
def search(request):
    db, token, uid = initializationDb()
    result = db.child(uid).child("tweet").get(token)
    return JsonResponse(result.val())


@require_http_methods(["GET"])
def retrieve_popular(request):
    db, token, uid = initializationDb()
    output = {}
    out = []
    result = db.child(uid).child("movie_popular").get(token)
    movies = result.val()
    for movie in movies:
        out.append(movies[movie])
    output['movies'] = out
    return JsonResponse(output)


@require_http_methods(["GET"])
def retrieve_movie(request):
    db, token, uid = initializationDb()
    result = db.child(uid).child("movie_list").get(token)
    single = int(request.GET.get('mode', 2))
    name = request.GET.get('query', 'Marlina')
    value = result.val()
    if single == 0:
        output = {}
        movies = []
        for res in value:
            if name in value[res]['title']:
                movies.append(value[res])
        output['movies'] = movies
        return JsonResponse(output)
    elif single == 1:
        output = {}
        out = []
        for res in value:
            if value[res]['title'] == name:
                out.append(value[res])
                break
        output['movies'] = out
        return JsonResponse(output)
    else:
        output = {}
        out = []
        for movie in value:
            out.append(value[movie])
        output['movies'] = out
        return JsonResponse(output)


@csrf_exempt
@require_http_methods(["POST"])
def traindata(request):
    try:
        db, token, uid = initializationDb()
        lang = request.POST.get("lang", "en")
        queryRaw = request.POST.get("query", "Film")
        count = int(request.POST.get("count", 10))
        query = queryRaw.split(';')
        tso = TwitterSearchOrder()
        tso.set_keywords(query)
        tso.set_include_entities(False)
        tso.set_count(count)
        if lang == 'en' or lang == 'id':
            tso.set_language(lang)

        ts = TwitterSearch(
            consumer_key=os.environ['consumerKey'],
            consumer_secret=os.environ['consumerSecret'],
            access_token=os.environ['accessToken'],
            access_token_secret=os.environ['accessTokenSecret']
        )
        response = []
        for tweet in ts.search_tweets_iterable(tso):
            # Pass the user's idToken to the push method
            response.append(tweet['text'])
        responseData = {}
        responseData['tweet'] = response
        return JsonResponse(responseData)
    except TwitterSearchException as e:
        return HttpResponse(e)
