"""dns URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from . import views
from main import views as main_views

# tastypie
from tastypie.api import Api
from dns.api import ZoneResource, RecordResource, ViewResource, ServerGroupResource, ServerResource, ServerConfigResource, RecordHistoryResource

v1_api = Api(api_name='v1')
v1_api.register(ServerGroupResource())
v1_api.register(ServerConfigResource())
v1_api.register(ServerResource())
v1_api.register(ViewResource())
v1_api.register(ZoneResource())
v1_api.register(RecordResource())
v1_api.register(RecordHistoryResource())

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(v1_api.urls)),
    url(r'^$', main_views.index, name='index'),
    url(r'^main/', include('main.urls', namespace='main')),
]
