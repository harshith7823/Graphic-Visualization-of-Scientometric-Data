from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^process/$', views.process, name='process'),#(?P<NAME>[\w\+\ ]+)
    #url(r'^dummy$', views.dummy, name='dummy'),
]