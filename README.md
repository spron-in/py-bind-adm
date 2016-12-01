# py-bind-adm
Django administration tool for the most popular DNS server Bind9 from ISC.

## License

MIT license, see LICENSE.txt for full text.

## Overview

Web administration tool to rule bind9 configuration and zones.  
Was used in production with a highload bind9 cluster with multiple views and 100+ zones.  
All bind zones and configuration is stored in backend database. I was using MySQL, you can use whatever Django is capable.  

What it can:

1. Deploy configuration to master and slaves
1. Edit and update zone, regenerate on master
1. Perform zone validation
1. Keep track on all the changes
1. Authorize and authenticate users based on their certificate

What it cannot:

1. Deploy bind9 instances/servers with all needed initial configurations
1. Handle balancing and other stuff. This thing is just for zone/config manipulations. Day-to-day things.

## Requirements and stack

Python3 is in use  
MySQL as backend DB  (Postgre will do as well)

**Web:**  
Django  
jQuery  
Bootstrap  
jsrender  
codemirror  
API on tastypie  

**From pip freeze:**
```
Django==1.9.2
django-simple-history==1.8.0
django-tastypie==0.13.3
gunicorn==19.4.5
ipaddress==1.0.16
mysqlclient==1.3.7
python-dateutil==2.4.2
python-mimeparse==1.5.1
PyYAML==3.11
requests==2.9.1
simplejson==3.8.2
six==1.10.0
```

## ToDo

1. Autogeneration of zones.conf
1. Add zone via main interface, not django admin (too lazy)
1. Documentation and installation howto
1. Fix minor bugs

## Disclaimer
We were using this thing in production for quite a long time, served us well. Use at your own risk.

## How to get help
Contact and follow me on twitter (@sergeypronin)
