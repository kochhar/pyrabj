'''
util.py

Utilities functions and class for using the Rabj APIs
'''
import logging, urlparse

try:
    import happy.json
    class json:
        loads = staticmethod(happy.json.decode)
        dumps = staticmethod(happy.json.encode)
        class JSONEncoder(object): pass
except ImportError:
    try:
        import json
    except ImportError:
        try:
            import simplejson as json
        except ImportError:
            raise ImportError("Cannot find happy.json, stdlib json or simplejson.")    

_log = logging.getLogger("pyrabj.util")

class EasyPeasyJsonEncoder(json.JSONEncoder):
    """ Class which provides json encoding facilities. Any object which has
    a jsonable method can be converted to json. The jsonable method should
    return a representation that is compatible with a json encoder -- i.e. a
    python built-in type"""
    
    def default(self, o):
        if hasattr(o, 'jsonable'):
            return o.jsonable()
        else:
            return super(RabjContainerEncoder, self).default(o)

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
 
