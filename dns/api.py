from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication, SessionAuthentication, MultiAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.validation import Validation
from tastypie.exceptions import BadRequest
from tastypie.utils import trailing_slash
from tastypie.cache import NoCache

from django.core.urlresolvers import resolve
from django.conf.urls import url
from django.core.validators import validate_ipv4_address, validate_ipv6_address
from django.db.models import Q
from django.contrib.auth.models import User

from main.models import Zone, Record, View, record_type_choices, zone_type_choices, ServerGroup, Server, ServerConfig
from dns.dns_system_actions import GenerateZone, SaveConfig, CloneZone
import re

class RecordValidation(Validation):

    def is_valid(self, bundle, request=None):

        if not bundle.data:
            return {'__all__': 'No parameters passed'}

        errors = {}

        record_type = int(bundle.data['record_type'])
        host = bundle.data['host']
        answer = bundle.data['answer']
        zone = bundle.data['zone']

        if 'record_id' in bundle.data:
            record_id = int(bundle.data['record_id'])
        else:
            record_id = False

        view, args, kwargs = resolve(zone)
        zone_pk = kwargs['pk']

        record_type_text = dict(record_type_choices).get(record_type)

        if self.if_duplicate(host, answer, zone_pk, record_id):
            errors['duplicate'] = ['Duplicated host and answer']

        if self.if_same_host(host, record_type_text, zone_pk, record_id):
            errors['duplicate'] = ['Same host detected. RFC violation.']

        if record_type_text == 'A':
            try:
                validate_ipv4_address(answer)
            except:
                errors['answer'] = ['Should be IPv4 address']

            if not self.if_hostname(host):
                errors['host'] = ['Should be valid hostname']

        elif record_type_text == 'AAAA':
            try:
                validate_ipv6_address(answer)
            except:
                errors['answer'] = ['Should be IPv6 address']

            if not self.if_hostname(host) or host == '@':
                errors['host'] = ['Should be valid hostname']

        elif record_type_text == 'CNAME':

            if not self.if_fqdn(answer):
                errors['answer'] = ['Should be valid FQDN']

            if not self.if_hostname(host):
                errors['host'] = ['Should be valid hostname']
           
        elif record_type_text == 'NS':

            if not self.if_fqdn(answer):
                errors['answer'] = ['Should be valid FQDN']

            if not self.if_hostname(host):
                errors['host'] = ['Should be valid hostname']

        elif record_type_text == 'MX':
        
            if not self.if_fqdn(answer):
                errors['answer'] = ['Should be valid FQDN']

            if not self.if_hostname(host):
                errors['host'] = ['Should be valid hostname']

        elif record_type_text == 'PTR':
        
            if not self.if_fqdn(answer):
                errors['answer'] = ['Should be valid FQDN']
 
        return errors

    def if_fqdn(self, hostname):
        if len(hostname) > 255:
            return False

        if hostname[-1] == ".":
            hostname = hostname[:-1]
        else:
            return False

        allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        return all(allowed.match(x) for x in hostname.split("."))

    def if_hostname(self, hostname):
        if len(hostname) > 255:
            return False

        if hostname[-1] == ".":
            return False

        if hostname == '@' or hostname == '*':
            return True

        if re.match('^\*\..+$', hostname):
            hostname = hostname.lstrip('*.')

        allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        return all(allowed.match(x) for x in hostname.split("."))

    def if_duplicate(self, host, answer, zone_pk, record_id):

        if record_id:
            rf = Record.objects.filter(~Q(pk=record_id),zone=zone_pk, host=host, answer=answer)
        else:
            rf = Record.objects.filter(zone=zone_pk, host=host, answer=answer)
        if rf:
            return True

        return False

    def if_same_host(self, host, record_type_text, zone_pk, record_id):

        record_type_list = []
        if record_type_text == 'CNAME':
            record_type_list.append(self.get_record_type_id_by_text('A'))
            record_type_list.append(self.get_record_type_id_by_text('CNAME'))
        elif record_type_text == 'A':
            record_type_list.append(self.get_record_type_id_by_text('CNAME'))
        elif record_type_text == 'PTR':
            record_type_list.append(self.get_record_type_id_by_text('PTR'))
        else:
            return False

        if record_id:
            rf = Record.objects.filter(~Q(pk=record_id),zone=zone_pk, host=host, record_type__in=record_type_list)
        else:
            rf = Record.objects.filter(zone=zone_pk, host=host, record_type__in=record_type_list)
            
        if rf:
            return True

        return False
        

    def get_record_type_id_by_text(self, record_type_text):
        
        return list(dict(record_type_choices).keys())[list(dict(record_type_choices).values()).index(record_type_text)]

class ServerResource(ModelResource):

    class Meta:
        queryset = Server.objects.all()
        resource_name = 'server'
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        authorization = DjangoAuthorization()

class ServerGroupResource(ModelResource):

    servers = fields.ManyToManyField(ServerResource, "servers", null=False, related_name="servergroup", full=True)

    class Meta:
        queryset = ServerGroup.objects.all()
        resource_name = 'servergroup'
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        authorization = DjangoAuthorization()


class ServerConfigResource(ModelResource):

    group = fields.ForeignKey(ServerGroupResource, "group", full=True)

    class Meta:
        queryset = ServerConfig.objects.all()
        resource_name = 'serverconfig'
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        authorization = DjangoAuthorization()

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/apply/(?P<config_id>[0-9]+)%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('apply_config'), name="api_record_apply_config"),
        ]

    def apply_config(self, request, **kwargs):
        
        apply_config = {}
#        self.method_check(request, allowed=['get'])

        config_id = kwargs['config_id']
        message = []
        try:
            sc = SaveConfig(config_id)
            message = sc.applyConfig()
        except Exception as e:
            raise BadRequest(str(e))
        
        apply_config['apply'] = message

        return self.create_response(request, apply_config)

class ViewResource(ModelResource):
    class Meta:
        queryset = View.objects.all()
        resource_name = 'view'
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        authorization = DjangoAuthorization()

class ZoneResource(ModelResource):

    view = fields.ForeignKey(ViewResource, 'view', full=True)

    class Meta:
        queryset = Zone.objects.all()
        resource_name = 'zone'
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        authorization = DjangoAuthorization()
        always_return_data = True

        filtering = {
            "zone": ALL,
        }
        max_limit = None 
    
    def dehydrate_type(self, bundle):

        bundle.data['type'] = dict(zone_type_choices).get(bundle.data['type'])

        return bundle.data['type']

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/clone%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('clone'), name="api_zone_clone"),
        ]

    def clone(self, request, **kwargs):
        
        clone = {}

        message = []

        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))

        try:
            cz = CloneZone(data['zone_id'], data['view_id'])    
            message = cz.cloneZone()
        except Exception as e:
            raise BadRequest(str(e))
        
        clone['clone'] = message

        return self.create_response(request, clone)

class RecordResource(ModelResource):
    zone = fields.ForeignKey(ZoneResource, 'zone', full=True)

    class Meta:
        queryset = Record.objects.all()
        resource_name = 'record'
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        authorization = DjangoAuthorization()
        validation = RecordValidation()
        always_return_data = True
        filtering = {
            "zone": ALL_WITH_RELATIONS,
            "host": ALL,
            "answer": ALL,
            "record_type": ALL
        }
        max_limit = None 

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/generate/(?P<zone_id>[0-9]+)%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('generate'), name="api_record_generate"),
        ]

    def generate(self, request, **kwargs):
        
        generate = {}
        self.method_check(request, allowed=['get'])

        zone_id = kwargs['zone_id']
        message = []
        try:
            gz = GenerateZone(zone_id)
            gz.updateSerial()
            message = gz.printZone()
        except Exception as e:
            raise BadRequest(str(e))
        
        generate['generate'] = message

        return self.create_response(request, generate)
    
    def hydrate_host(self, bundle):

        bundle.data['success'] = 1
        if not 'host' in bundle.data or not bundle.data['host']:
            bundle.data['host'] = '@'

        return bundle
       

    def hydrate_ttl(self, bundle):

        if not 'ttl' in  bundle.data or bundle.data['ttl']:
            bundle.data['ttl'] = 600

        return bundle 

    def hydrate_record_type(self, bundle):
        
        if 'record_type_text' in bundle.data:
            try:
                bundle.data['record_type'] = list(dict(record_type_choices).keys())[list(dict(record_type_choices).values()).index(bundle.data['record_type_text'])]
            except:
                return bundle
        return bundle        

    def dehydrate_record_type(self, bundle):

        bundle.data['record_type_text'] = dict(record_type_choices).get(bundle.data['record_type'])

        return bundle.data['record_type']
    

class DjangoUserResource(ModelResource):
    
    class Meta:
        queryset = User.objects.all()
        resource_name = "users"
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        authorization = DjangoAuthorization()
        always_return_data = True
        list_allowed_methods = ['get']
        excludes = ['email', 'is_active', 'password', 'last_login', '_password', 'is_staff', 'id', 'date_joined']

class RecordHistoryResource(ModelResource):
    zone = fields.ForeignKey(ZoneResource, 'zone', full=True)
    history_user = fields.ForeignKey(DjangoUserResource, 'history_user', full=True)

    class Meta:
        queryset = Record.history.all()
        resource_name = 'rhistory'
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        authorization = DjangoAuthorization()
        always_return_data = True
        list_allowed_methods = ['get']
        filtering = {
            "zone": ALL_WITH_RELATIONS,
            "host": ALL,
            "answer": ALL,
            "record_type": ALL
        }
        max_limit = 100

    def dehydrate_record_type(self, bundle):

        bundle.data['record_type_text'] = dict(record_type_choices).get(bundle.data['record_type'])

        return bundle.data['record_type']

    def dehydrate_history_date(self, bundle):

        bundle.data['history_date'] = bundle.data['history_date'].strftime('%Y-%m-%d %H:%M:%S')

        return bundle.data['history_date']
    
