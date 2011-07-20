'''
containers.py

module containing containers for rabj objects
'''
import cStringIO, logging, pprint
import util as u
from util import json
_log = logging.getLogger("pyrabj.containers")

try:
    from collections import MutableSequence, MutableMapping
except ImportError:
    """Jython 2.5 doesn't include Mapping and MutableSequence in its
    collections module. They are copied to the jycompat module."""
    from jycompat.collections import MutableSequence, MutableMapping

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
    """Abstract container for Rabj data."""

    def __init__(self, data, url, *args, **kwargs):
        """Initializer for a new rabj container. The only argument is the data
        object contained"""
        super(RabjContainer, self).__init__()
        self.data = data
        self.url = url
        self.container_factory = RabjContainerFactory(self.url)

    def copy_from_other(self, other):
        """
        Soft-copies data from another container to this container
        """
        self.data = other.data
        self.url = other.url
        self.container_factory = other.container_factory

    def __repr__(self):
        return repr(self.data)

    def __str__(self):
        strbuf = cStringIO.StringIO()
        pprint.pprint(self.data, strbuf)
        rabjstr = strbuf.getvalue()
        strbuf.close()
        return rabjstr

    def tojson(self):
        """Convert the object to it's json representation."""
        return json.dumps(self.jsonable())

    def jsonable(self):
        return self.data

from rabj.api import RabjCallable
class RabjDict(RabjContainer, MutableMapping):
    """Mapping container for rabj responses. Finds urls within the rabj
    response and converts them into RabjCallables The RabjDict itself is a
    RabjCallable object and provides access to HTTP methods on the url which
    identifies the object.

    RabjDicts provide attribute style access to attributes which might not
    exist on the object. These attributes are mapped into the url space of the
    location of the RabjDict.

    RabjDicts provide similar access to keys which might not be contained
    within the keys. These keys are also mapped into the url space of the
    location of the RabjDict

    This sounds very complicated but in essence allows you to do things like:

    >>> myqueue = RabjDict(result=None, url=my_queue_url)
    >>> # equivalent to a HTTP GET on my_queue_url+'/judgments'
    >>> myqueue.judgments.get()
    """
    def __init__(self, result, url, *args, **kwargs):
        """Initializes a RabjDict object. The result is the mapping object and
        the url is the remote location of the object."""
        super(RabjDict, self).__init__(data=result, url=url, *args, **kwargs)

        access_key = self.data.get('__metadata__', {}).get('access_key', self.data.get('access_key'))
        self.rabjcallable = RabjCallable(url, access_key)

    def copy_from_other(self, other):
      """Copy from a rabj dict from another"""
      super(RabjDict, self).copy_from_other(other)
      self.rabjcallable = other.rabjcallable
    
    def __getattr__(self, attr):
        """The method which provides attribute like access to the URL space."""
        return getattr(self.rabjcallable, attr)

    def __getitem__(self, key):
        """The method which provides key like access to the URL space."""
        try:
            item = self.data[key]
            return self.container_factory.container(item)
        except KeyError, e:
            return self.rabjcallable[key]

    def __setitem__(self, key, item):
        """Dict-like setitem method"""
        self.data[key] = item

    def __delitem__(self, key):
        """Dict-like delitem method"""
        del self.data[key]

    def http_get(self, **kwargs):
        """Invokes a HTTP get on the URL contained in the RabjCallable in this
        RabjDict. kwargs are turned into get params"""
        return self.rabjcallable.get(**kwargs)

    def http_post(self, **kwargs):
        """Invokes a HTTP post on the URL contained in the RabjCallable in
        this RabjDict. kwargs are encoded as json and sent along as the
        request body."""
        return self.rabjcallable.post(**kwargs)

    def http_put(self, **kwargs):
        """Invokes a HTTP put on the URL contained in the RabjCallable in this
        RabjDict. kwargs are encoded as json and sent along as the request
        body."""
        return self.rabjcallable.put(**kwargs)

    def http_delete(self, **kwargs):
        """Invokes a HTTP delete on the URL contained in the RabjCallable in
        this RabjDict. kwargs are encoded as json and sent along as the
        request body."""
        return self.rabjcallable.delete(**kwargs)

    def __iter__(self):
        """Iterator over the items in the dict"""
        return iter(self.data)

    def __len__(self):
        """Length of the dict"""
        return len(self.data)

class RabjList(RabjContainer, MutableSequence):
    """Sequence container for rabj responses. Elements of the list which are
    dicts having an 'id' field are transformed into RabjDicts.

    A RabjList is not quite as sophisticated as a RabjDict but the general
    idea is the same -- facilitating access to the Rabj API in an object-like
    manner.
    """
    def __init__(self, result, url, *args, **kwargs):
        super(RabjList, self).__init__(data=result, url=url, *args, **kwargs)

    def __getitem__(self, i):
        item = self.data[i]
        return self.container_factory.container(item)

    def __setitem__(self, i, item):
        self.data[i] = item

    def __delitem__(self, i):
        del self.data[i]

    def __len__(self):
        return len(self.data)

    def insert(self, i, item):
        return self.data.insert(i, item)
