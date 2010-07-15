import logging, httplib2, urllib
from rabj import VERSION, APP
import util as u
from util import json, EasyPeasyJsonEncoder

_def_headers = { 'Accept': 'application/json',
                 'Content-type': 'application/json',
                 'User-agent': ':'.join([APP, "pyrabj.api", VERSION])
               }

_log = logging.getLogger("pyrabj.api")

"""
httplib2 requires the idna encoder to convert IRIs to URIs. Jython
does not yet support idna encoding, so httplib2 will always fail.
We can register ascii as "idna" to work around this problem, and
just let internationalized domain names fail to resolve.
"""
import codecs
try:
    codecs.lookup("idna")
except LookupError:
    def find_idna(name):
        if name == "idna":
            return codecs.lookup("ascii")
    codecs.register(find_idna)

class RabjCallable(object):
    """
    A minimalist yet fully featured implementation to use the RABJ API. A
    RabjCallable instance points at a url. URL heirarchies are traversed by
    accessing attributes of a RabjCallable. For instance::

        >>> rabj = RabjCallable('http://data.labs.freebase.com/rabj/')
        >>> print rabj.store._url
        http://data.labs.freebase.com/rabj/store/
        >>> public_queues = rabj.store.queues.public
        >>> print public_queues._url
        http://data.labs.freebase.com/rabj/store/queues/public/
        
    The methods of a RabjCallable instance (:meth:`get`, :meth:`post`,
    :meth:`put`, :meth:`delete`) translate to their HTTP equivalents. This
    provides a very lightweight wrapper for the RESTful API. The results of
    invoking a method is a tuple of a :class:`~rabj.api.RabjResponse` and a
    :class:`~rabj.containers.RabjContainer` which holds the unwrapped
    results::

        >>> resp, result = public_queues.get()
        >>> type(resp)
        <class 'rabj.api.RabjResponse'>
        >>> type(result)
        <class 'rabj.containers.RabjList'>
        
    **Examples**
    ::
    
        >>> rabj = RabjCallable('http://data.labs.freebase.com/rabj/')
        
        # Get a list of queues with my tags
        >>> mytags = [ 'foo', 'bar' ]
        >>> resp, myqs = rabj.store.queues.tags.get(tag=mytags)
        
        # Get a particular queue
        >>> resp, myq1 = rabj.store.queues['queue_124113044366_0'].get()
        >>> print myq1['id']
        /rabj/store/queues/queue_124113044366_0
        
        # Also supported (but totally weird)
        >>> resp2, myq2 = rabj.store.queues.queue_124113044366_0.get()
        >>> resp3, myq3 = getattr(rabj.store.queues, 'queue_124113044366_0').get()
        
        # create a new queue
        >>> queue = {'name': 'my dr suess queue',
                     'owner': '/user/dr_seuss', 
                     'tags': ['/en/cat', '/en/hat'],
                     'votes': 2}                 
        >>> resp, qcreate = rabj.store.queues.post(queue=queue)
        >>> qid = qcreate['id']
        
        # Add a list of questions to the newly created queue
        >>> resp, addq = qcreate.questions.post(questions=generate_questions(10))
    
    **Using the data returned**
    
    The RabjContainer objects returned play a dual-role. First, they act as
    containers like their python equivalantes (lists and
    dicts). RabjContainers also provide the ability to make further Rabj
    calls::
    
        >>> resp, queue = rabj.store.queues['queue_124113044366_0'].questions.get()

        # All questions on the queue
        >>> queue_questions = queue['questions']
        >>> type(queue_questions)
        <class 'rabj.containers.RabjList'>
        >>> print queue_questions

        # The first question on the queue
        >>> ques0ref = queue_questions[0]
        >>> type(ques0ref)
        <class 'rabj.containers.RabjDict'>
        >>> print ques0ref

        # Get the question 
        >>> resp, question = ques0ref.get()
        >>> print question

        # Retrieve a list of completed questions for a queue
        >>> resp, queue_comp = rabj.store.queues['queue_124113044366_0'].questions.complete.get()
        >>> completed_questions = queue_comp['questions']
    
        # fetch the list of users who have answered the second question
        >>> resp, qq2_users = completed_questions[2].users.get()
     
        # fetch the list of judgments for all the completed questions
        >>> fetches = [ q.judgments.get() for q in completed_questions ]
        >>> judgments = [ result['judgments'] for (resp, result) in fetches ]        
    """
    def __init__(self, url, access_key=None, *args, **kwargs):
        super(RabjCallable, self).__init__(*args, **kwargs)
        self._url = url if url.endswith('/') else url + '/'
        self._access_key = access_key
        self._http = httplib2.Http()
        
    def __repr__(self):
        return "<%s@%s>" % (self.__class__.__name__, self._url)

    def __getattr__(self, attr):
        try:
            return super(RabjCallable, self).__getattr__(attr)
        except AttributeError:
            return self[attr]
    
    def __getitem__(self, key):
        return RabjCallable(self._url+key, access_key=self._access_key)
    
    def get(self, **kwargs):
        """Execute a HTTP GET request on the current url. Additional
        parameters passed as kwargs will be added as query params.
        """
        return self.response(*self.request_params(self._url, "GET", **kwargs))

    def post(self, **kwargs):
        """Execute a HTTP POST request on the current url. Additional
        parameters passed as kwargs will be encoded as JSON and sent in the
        body.
        """
        return self.response(*self.request_params(self._url, "POST", **kwargs))
        
    def put(self, **kwargs):
        """Execute a HTTP PUT request on the current url. Additional
        parameters passed as kwargs will be encoded as JSON and sent in the
        body.
        """
        return self.response(*self.request_params(self._url, "PUT", **kwargs))

    def delete(self, **kwargs):
        """Execute a HTTP DELETE request on the current url. Additional
        parameters passed as kwargs will be encoded as JSON and sent in the
        body.
        """        
        return self.response(*self.request_params(self._url, "DELETE", **kwargs))

    def request_params(self, url, method, **kwargs):
        """
        Constructs the parameters for a http request
        """
        params = dict()
        if self._access_key is not None:
            params['access_key'] = self._access_key

        if kwargs:
            params.update(kwargs)

        if method == "GET":
            url = url + "?" + urllib.urlencode(params, doseq=True)
            body = None
        else:
            body = json.dumps(params, cls=EasyPeasyJsonEncoder)

        return url, method, body, _def_headers
    
    def response(self, url, method, body, headers):
        """
        Executes the request and wraps into a RabjResponse
        """
        _log.debug("Sending %s to url %s", method.lower(), url)
        resp, content = self._http.request(url, method, body, headers)
        rabj_resp = RabjResponse(content, resp, url)
        return rabj_resp, rabj_resp.result

import containers as c
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
        return "%s@%s" % (self.__class__.__name__, self._url)
    
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
                envelope = json.loads(content)
                if envelope['status']['code']  == 200:
                    return envelope
                else:
                    error = envelope['error']
                    raise RabjError(error['code'], error['class'], error['detail'], envelope)
            except ValueError, e:
                _log.warn("Decode error %s in content %s", e, content)
                raise RabjError(resp.status, resp.reason, {'msg': e.message}, content)
        else:
            _log.warn("Non-json response '%s' when fetching %s",
                      content, resp.get('content-location', self._url))
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


__all__ = [ 'RabjCallable', 'RabjResponse' , 'RabjError' ]
