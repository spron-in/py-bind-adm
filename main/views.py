from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.contrib.auth.decorators import permission_required
from django.db.models import Q

from .models import View, Zone, Record, record_type_choices, ServerConfig, Check

from dns.config import config
from dns.dns_health_check import CheckHealthActions

import math

# Create your views here.
def index(request):

    if not request.user.is_authenticated():
        return render(request, 'main/not_authorized.html')

    return render(request, 'main/zones.html')

def records(request, zone_id):

    if not request.user.is_authenticated():
        return render(request, 'main/not_authorized.html')

    # get zone
    zone = get_object_or_404(Zone, pk=zone_id)

    # get views pk for this zone
    views_list = []
    zone_list = Zone.objects.filter(zone=zone.zone)
    for zone_v in zone_list:
         views_list.append(zone_v.view.pk)

    cloneViews = View.objects.exclude(pk__in=views_list)

    context = {
        'zone': zone,
        'zone_list': zone_list,
        'record_type_choices': record_type_choices,
        'default_ttl': config['dns']['default']['ttl'],
        'cloneViews': cloneViews,
    }

    return render(request, 'main/records.html', context)

def recordSearch(request):

    if not request.user.is_authenticated():
        return render(request, 'main/not_authorized.html')

    context = {}

    return render(request, 'main/recordSearch.html', context)

@permission_required('serverconfig.can_open', login_url='/main/noauth/')
def configs(request):

    if not request.user.is_authenticated():
        return render(request, 'main/not_authorized.html')

    configs = ServerConfig.objects.all()

    context = {
        'configs': configs,
    }

    return render(request, 'main/configs.html', context)

@permission_required('serverconfig.can_open', '/main/noauth/')
def configDetail(request, config_id):

    if not request.user.is_authenticated():
        return render(request, 'main/not_authorized.html')

    serverConfig = get_object_or_404(ServerConfig, pk=config_id)

    context = {
        'serverConfig': serverConfig,
    }

    return render(request, 'main/configDetail.html', context)

@permission_required('serverconfig.can_open', '/main/noauth/')
def configGenerate(request):

    if not request.user.is_authenticated():
        return render(request, 'main/not_authorized.html')

    zones = Zone.objects.all()
    context = {
        'zones': zones,
    }

    return render(request, 'main/configGenerate.html', context)

def health(request):

    checks = Check.objects.values()

    for check in checks:
        check['result'] = 0
        check['message'] = ''
    
        cha = CheckHealthActions(check)
        check = cha.run()
    
    context = {
        'checks': checks,
    }

    return render(request, 'main/health.html', context)


def healthRun(request):

    checks = Check.objects.values()

    health = 0
    for check in checks:
        check['result'] = 0
        check['message'] = ''
    
        cha = CheckHealthActions(check)
        check = cha.run()

        if check['result'] != 0:
            health = 1

    return HttpResponse(health)

def noauth(request):

    return render(request, 'main/not_authorized.html')

def recordHistory(request):

    if not request.user.is_authenticated():
        return render(request, 'main/not_authorized.html')

    context = {}

    return render(request, 'main/recordHistory.html', context)
