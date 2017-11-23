from django.shortcuts import render
from django.http import HttpResponse
import requests
import json


def index(request):
    url_film = 'http://twitter-crawler-data.herokuapp.com/api/release'
    image_base = 'https://image.tmdb.org/t/p/w500/'
    payload = {'mode': 0, 'query': ''}
    req = requests.get(url_film, params=payload)
    jsonData = json.loads(req.text)
    return render(request, 'index.html', {'film_data': jsonData['movies'], 'image_base': image_base})