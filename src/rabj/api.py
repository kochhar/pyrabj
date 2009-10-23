import logging, httplib2, jsonlib2, sys, urllib
from rabj import VERSION as clientversion
import containers as c, util as u


_def_headers = { 'Accept': 'application/json',
                 'Content-type': 'application/json',
                 'User-agent': '%srabjclient/%s' % (sys.argv[0] and sys.argv[0]+' ' or '', clientversion)
               }

_log = logging.getLogger("pyrabj.api")

class RabjCallable(object):
    """
    The minimalist yet fully featured Rabj API class.

    Get RESTful data by accessing members of this class. The result
    is decoded python objects (lists and dicts).

    The Rabj API is documented here:
    https://wiki.metaweb.com/index.php/RABJ/API

    Examples::

    >>> rabj = RabjCallable('http://dw01.corp/rabj')

    # Get a list of queues with my tags
    >>> mytags = [ 'foo', 'bar' ]
    >>> myqs = rabj.store.queues.tags.get(tag=mytags)

    # Get a particular queue
    >>> myq1 = rabj.store.queues['queue_124113044366_0'].get()
    >>> print myq.result['id']
    /rabj/store/queues/queue_124113044366_0

    # Also supported (but totally weird)
    >>> myq2 = rabj.store.queues.queue_124113044366_0.get()
    >>> myq3 = getattr(rabj.store.queues, 'queue_124113044366_0').get()

    # create a new queue
    >>> queue = {'name': 'my dr suess queue',
                 'owner': '/user/dr_seuss', 
                 'tags': ['/en/cat', '/en/hat'],
                 'votes': 2}                 
    >>> qcreate = rabj.store.queues.post(queue=queue).result
    >>> qid = qcreate['id']
    
    # Add a list of questions to the newly created queue
    >>> addq = qcreate.questions.post(questions=generate_questions(10))
    
    Using the data returned::

    Rabj client calls return decoded JSON wrapped in an object which allows you
    to make further Rabj calls. For example,

    # Retrieve a list of all questions for a queue
    >>> qq = rabj.store.queues['queue_124113044366_0'].questions.get().result
    >>> ques1_id = qq['questions'][0]['id']
    >>> ques1 = qq['questions'][0].get()

    # Retrieve a list of completed questions for a queue
    >>> completed = qq.questions.complete.get().result
    >>> completed_questions = completed['questions']
    
    # fetch the list of users who have answered the second question
    >>> qq2_users = completed_questions[2].users.get()
    
    # fetch the list of judgments for all the completed questions
    judgments = [ q.judgments.get() for q in completed_questions ]
    """
    def __init__(self, url, access_key=None, *args, **kwargs):
        _log.debug("RabjCallable.__init__")
        super(RabjCallable, self).__init__(*args, **kwargs)
        self.host_url = u.host_url(url)
        self.path = u.path(url)
        self.access_key = access_key
        self.rabjcall = RabjCall(self.base_url, self.access_key)

    def __getattr__(self, attr):
        _log.debug('RabjCallable.__getattr__(%s)', attr)
        try:
            return super(RabjCallable, self).__getattr__(attr)
        except AttributeError:
            return self[attr]
    
    def __getitem__(self, key):
        _log.debug('RabjCallable.__getitem__(%s)', key)
        return RabjCallable(self.base_url+"/"+key, self.access_key)

    @property
    def base_url(self):
        if self.path == "/":
            base_url = "%s" % (self.host_url)
        else:
            base_url = "%s%s" % (self.host_url, self.path)

        return base_url

    def get(self, **kwargs):
        return self.rabjcall.get(**kwargs)

    def post(self, **kwargs):
        return self.rabjcall.post(**kwargs)

    def put(self, **kwargs):
        return self.rabjcall.put(**kwargs)

    def delete(self, **kwargs):
        return self.rabjcall.delete(**kwargs)


class RabjCall(object):
    """Encapsulates a call to Rabj
    """
    def __init__(self, url, access_key, *args, **kwargs):
        self.url = url
        self.access_key = access_key
        self.http = httplib2.Http()

    def __repr__(self):
        return "<%s@%s>" % (self.__class__.__name__, self.url)

    def get(self, **kwargs):
        _log.debug('RabjCall.get(%s)', ", ".join(["%s=%s" %(k, v) for (k, v) in  kwargs.items()]))
        return self.http_request(self.url, "GET", **kwargs)
    
    def post(self, **kwargs):
        _log.debug('RabjCall.post(%s)', ", ".join(["%s=%s" % (k, v) for (k, v) in kwargs.items()]))
        return self.http_request(self.url, "POST", **kwargs)
        
    def put(self, **kwargs):
        _log.debug('RabjCall.put(%s)', ", ".join(["%s=%s" % (k, v) for (k, v) in kwargs.items()]))
        return self.http_request(self.url, "PUT", **kwargs)

    def delete(self, **kwargs):
        _log.debug('RabjCall.delete(%s)', ", ".join(["%s=%s" % (k, v) for (k, v) in kwargs.items()]))
        return self.http_request(self.url, "DELETE", **kwargs)

    def http_request(self, url, method, **kwargs):
        params = { 'access_key': self.access_key }

        if kwargs:
            params.update(kwargs)
        
        if method == "GET":
            url = url + "?" + urllib.urlencode(params, doseq=True)
            body = None
        else:
            body = jsonlib2.dumps(params, escape_slash=False)

        _log.debug("Sending %s to url %s", method.lower(), url)
        resp, content = self.http.request(url, method, body, _def_headers)
        rabj_resp = RabjResponse(content, resp, url)
        return rabj_resp, rabj_resp.result
    
class RabjResponse(object):
    """Container for a response from rabj with convenience methods
    """
    def __init__(self, content, resp, url, *args, **kwargs):
        super(RabjResponse, self).__init__()
        self._url = url
        self.http_resp = resp
        self.env = self._parse(resp, content)
        self.container_factory = c.RabjContainerFactory(url)
        
    def __repr__(self):
        return "%s@%s" % (self.__class__.__name__, self.url)
    
    def __str__(self):
        return str(self.envelope)

    @property
    def url(self):
        return self._url

    @property
    def response(self):
        return self.http_resp

    @property
    def envelope(self):
        return self.env

    @property
    def result(self):
        """Unwraps the response envelope and returns the result of the
        operation as a rabj container
        """
        result = self.envelope['result']
        return self.container_factory.container(result)
        
    def _parse(self, resp, content):
        """Parses a rabj response to get the envelope information
        """
        if resp['content-type'] == 'application/json':
            try:
                envelope = jsonlib2.loads(content)
                if envelope['status']['code']  == 200:
                    return envelope
                else:
                    error = envelope['error']
                    raise RabjError(error['code'], error['class'], error['detail'], envelope)
            except jsonlib2.ReadError, e:
                _log.warn("Decode error %s in content %s", e, content)
                raise RabjError(resp.status, resp.reason, {'msg': e.message}, content)
        else:
            _log.warn("Non-json response '%s' when fetching %s",
                      content, resp.get('content-location', self.url))
            raise RabjError(resp.status, resp.reason, {'msg': content}, content)


class RabjError(Exception):
    """Exception class for errors from rabj. Provides access to error_code,
    error_class, msg, alt, where
    """    
    def __init__(self, error_code, error_class, detail, envelope):
        super(RabjError, self).__init__()
        self.env = envelope
        self.error_code = error_code
        self.error_class = error_class
        self.msg = detail['msg']
        self.alt = detail.get('alternatives')
        self.where = detail.get('in')
        
    def __str__(self):
        str_base = "%s %s. Msg: %s. " % (self.error_code, self.error_class, self.msg)
        if self.where: str_base += "Error in %s" % (self.where, )
        if self.alt: str_base += " try %s instead" % (self.alt, )

        return str_base

    @property
    def envelope(self):
        return self.env


__all__ = [ 'RabjCallable', 'RabjCall', 'RabjResponse' , 'RabjError' ]
