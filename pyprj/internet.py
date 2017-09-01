from __future__ import unicode_literals

import requests


try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

def absolute_url(url):
    i = url.find('/../') + 1
    return urljoin(url[:i], url[i:])

def internet_content(url, type_='text'):
    resp = requests.get(url)
    if resp.ok:
        return getattr(resp, type_)
    msg = "Failure while requesting %s: " % url
    raise RuntimeError(msg + str(resp.status_code))
