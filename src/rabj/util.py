'''
util.py

Utilities functions and class for using the Rabj APIs
'''
import logging, urlparse

try:
    import json
except ImportError:
    import simplejson as json

_log = logging.getLogger("pyrabj.util")

class NullHandler(logging.Handler):
    """
    Simple class for for doing nothing when logging. Used to add a simple
    handler and prevent logging config warning messages
    """
    def emit(self, record):
        pass
    

def host_url(url):
    """
    The URL through the host (no path)
    """
    pr = urlparse.urlsplit(url)

    scheme = pr.scheme
    host = pr.netloc
    
    url = '%s://%s' % (scheme, host)
    return url

def path(url):
    """
    The path of the URL after the host
    """
    pr = urlparse.urlsplit(url)
    return pr.path
 
