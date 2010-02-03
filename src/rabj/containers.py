'''
containers.py

module containing containers for rabj objects
'''
import jsonlib2, collections, cStringIO, logging, pprint
import util as u

_log = logging.getLogger("pyrabj.containers")

class RabjContainerFactory(object):
    def __init__(self, url):
        self.url = url
        self.host_url = u.host_url(url)
        self.path = u.path(url)

    def container(self, obj):
        if isinstance(obj, dict):
            # A dict response may be a rabj object with an id. If so, set the
            # path to be the id of the returned object
            if 'id' in obj:
                return RabjDict(obj, "%s%s" % (self.host_url, obj['id']))
            else:
                return obj
        elif isinstance(obj, list):
            return RabjList(obj, self.url)
        else:
            return obj

class RabjContainer(object):
    """Abstract container for Rabj data.
    """
    def __init__(self, data, url):
        super(RabjContainer, self).__init__()
        self.data = data
        self.url = url
        self.container_factory = RabjContainerFactory(self.url)
        
    def __repr__(self):
        return repr(self.data)

    def __str__(self):
        strbuf = cStringIO.StringIO()
        pprint.pprint(self.data, strbuf)
        rabjstr = strbuf.getvalue()
        strbuf.close()
        return rabjstr

    def json(self):
        """
        Convert the object to it's json representation
        """
        return jsonlib2.dumps(self.data)
    
    
from rabj.api import RabjCallable
class RabjDict(RabjContainer, collections.Mapping):
    """Mapping container for rabj responses
    """
    def __init__(self, result, url, *args, **kwargs):
        super(RabjDict, self).__init__(data=result, url=url)
        self.rabjcallable = RabjCallable(url, self.data.get('__metadata__', {}).get('access_key', self.data.get('access_key')))
        
    def __getattr__(self, attr):
        try:
            return super(RabjDict, self).__getattr__(attr)
        except AttributeError, e:
            return getattr(self.rabjcallable, attr)
    
    def __getitem__(self, key):
        try:
            item = self.data[key]
            return self.container_factory.container(item)
        except KeyError, e:
            return self.rabjcallable[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        try:
            del self.data[key]
        except KeyError, e:
            raise KeyError(e)
            
    def get(self, key=None, **kwargs):
        if key is None:
            return self.rabjcallable.get(**kwargs)

        return super(RabjDict, self).get(key)

    def post(self, **kwargs):
        return self.rabjcallable.post(**kwargs)

    def put(self, **kwargs):
        return self.rabjcallable.put(**kwargs)
    
    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)
    
class RabjList(RabjContainer, collections.MutableSequence):
    """Sequence container for rabj responses
    """
    def __init__(self, result, url):
        super(RabjList, self).__init__(data=result, url=url)

    def __getitem__(self, i):
        item = self.data[i]
        return self.container_factory.container(item)

    def __setitem__(self, i, item):
        self.data[i] = item

    def __delitem__(self, i):
        del self.data[i]

    def insert(self, i, item):
        return self.data.insert(i, item)
    
    def __len__(self):
        return len(self.data)
