import re

def parse_cert(dn):
    
    ret = dict()
    m = re.search(r"CN=(.+)/emailAddress=([a-z0-9-@\.+]+)", dn, re.IGNORECASE)
    if m: 
        ret['username'] = m.group(1)
        ret['email'] = m.group(2)

    return ret
