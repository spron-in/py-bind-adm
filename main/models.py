from django.db import models
from datetime import datetime
from simple_history.models import HistoricalRecords

record_type_choices = (
    (1, 'A'),
    (2, 'AAAA'),
    (3, 'MX'),
    (4, 'NS'),
    (5, 'TXT'),
    (6, 'SRV'),
    (7, 'CNAME'),
    (8, 'SPF'),
    (9, 'PTR'),
)

zone_type_choices = (
    (1, 'master'),
    (2, 'slave'),
    (3, 'forward')
)

config_type_choices = (
    (1, 'local'),
    (2, 'remote')
)

# Create your models here.
class View(models.Model):

    view = models.CharField(max_length=250, unique=True)
    comment = models.CharField(max_length=250)
    history = HistoricalRecords()

    def __str__(self):
        return self.view

class Server(models.Model):

    server = models.CharField(max_length=250, unique=True)
    comment = models.CharField(max_length=250)
    history = HistoricalRecords()

    def __str__(self):
        return self.server

class Zone(models.Model):

    zone = models.CharField(max_length=250)
    view = models.ForeignKey(View)
    ttl = models.PositiveIntegerField(default=600)
    origin = models.CharField(max_length=250)
    mail_addr = models.CharField(max_length=250)
    serial = models.PositiveIntegerField(default=1)
    refresh = models.PositiveIntegerField(default=7200)
    retry = models.PositiveIntegerField(default=3600)
    expire = models.PositiveIntegerField(default=1209600)
    minimum = models.PositiveIntegerField(default=600)
    type =  models.PositiveIntegerField(choices=zone_type_choices)
    history = HistoricalRecords()

    def __str__(self):
        return self.zone

class Record(models.Model):

    zone = models.ForeignKey(Zone)
    host = models.CharField(max_length=250)
    record_type = models.PositiveIntegerField(choices=record_type_choices, default=1)
    answer = models.CharField(max_length=250)
    ttl = models.PositiveIntegerField(default=600)
    priority = models.PositiveIntegerField(default=0)
    history = HistoricalRecords()

    def __str__(self):
        return "%s.%s" % (self.host, self.zone)

class ServerGroup(models.Model):

    group = models.CharField(max_length=250, unique=True)
    servers = models.ManyToManyField(Server)
    history = HistoricalRecords()

    def __str__(self):
        return self.group

class ServerConfig(models.Model):

    group = models.ForeignKey(ServerGroup)
    config = models.TextField(default='')
    type = models.PositiveIntegerField(choices=config_type_choices, default=2)
    name = models.CharField(max_length=250, default="zones.conf")
    history = HistoricalRecords()

    def __str__(self):
        return "%s - %s" % (str(self.group), self.name)

class CheckType(models.Model):

    type = models.CharField(max_length=250, unique=True)
    comment = models.CharField(max_length=250, default='')

    def __str__(self):
        return self.type

class Check(models.Model):

    type = models.ForeignKey(CheckType)
    check = models.CharField(max_length=250)
    parameter = models.TextField(default='')

    def __str__(self):
        return self.check
