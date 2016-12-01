from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

# Register your models here.
from .models import View, Server, Zone, Record, ServerGroup, ServerConfig, CheckType, Check

admin.site.register(View)
admin.site.register(Server)
admin.site.register(Zone)
admin.site.register(Record)
admin.site.register(ServerGroup)
admin.site.register(ServerConfig)
admin.site.register(CheckType)
admin.site.register(Check)
