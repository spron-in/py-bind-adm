from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^zones/$', views.index, name='index'),
    url(r'^zone/(?P<zone_id>.+)/$', views.records, name='records'),
    url(r'^record/search/$', views.recordSearch, name='recordSearch'),
    url(r'^record/history/$', views.recordHistory, name='recordHistory'),
    url(r'^configs/$', views.configs, name='configs'),
    url(r'^config/(?P<config_id>[0-9]+)/$', views.configDetail, name='configDetail'),
    url(r'^config/generate/$', views.configGenerate, name='configGenerate'),
    url(r'^health/$', views.health, name='health'),
    url(r'^health/run/$', views.healthRun, name='healthRun'),
    url(r'^noauth/$', views.noauth, name='noauth'),
]
