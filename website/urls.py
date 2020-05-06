from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^details/$', views.website),
    url(r'^session/details/$', views.website_session),
]