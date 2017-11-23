from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'search', views.search, name='search'),
    url(r'about', views.about, name='about')
]