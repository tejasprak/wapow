from django.urls import path
from django.conf.urls import url

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('eval', views.eval, name='eval'),
    path('rapm', views.rapm, name='rapm'),
    path('calculate_rapm', views.calculate_rapm, name='calculate_rapm'),
    url(r'^player/(?P<player_name_url>\w+)/$', views.player, name='player'),
]
