'''
util.py

Utilities functions and class for using the Rabj APIs
'''
import httplib2, logging, multiprocessing, urlparse
from Queue import Queue, Empty, Full

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


class Fetcher(multiprocessing.Process):
    """
    Extension to multiprocessing.Process class which takes a queue of tasks and a
    queue of results. Thread continues to run until the task queue is
    empty.

    The task queue should contain tuples of the form, (callable, *args,
    **kwargs).

    tasks    
        multiprocessing.Queue of tasks to be completed, each queue item should be a tuple
        containing (url, method, body, headers)

    results
        multiprocessing.Queue where results of invoking callable(*args,
        **kwargs) will be written

    args
        positional arguments to be passed to multiprocessing.Process(...)

    kwargs
        key-word arguments to be passed to multiprocessing.Process(...)
    """
    def __init__(self, tasks, results, *args, **kwargs):
        assert 'target' not in kwargs
        
        super(Fetcher, self).__init__(*args, **kwargs)
        self.tasks = tasks
        self.results = results
        self.shutdown = multiprocessing.Event()
        self.count = 0
        
    def stop(self):
        self.shutdown.set()
    
    def run(self):
        http = httplib2.Http()
        while not self.shutdown.is_set():
            try:
                url, method, body, headers = self.tasks.get(block=True, timeout=1)
                _log.debug("Sending %s to url %s", method.lower(), url)
                resp, content = http.request(url, method, body)
                self.results.put((url, (resp, content)))
                self.tasks.task_done()
                self.count += 1
            except Empty:
                pass

        _log.debug("shutting down process %s, executed %i tasks", self.name, self.count)
    
_poollog = logging.getLogger("pyrabj.util.http_pool")

class HTTPPool(object):
    """
    Implementation of a thread-safe http pool.

    timeout
        timeout for each individual connection, can be a float. None disables
        timeout.

    max
        Maximum number of connections which will be pooled for reuse. Setting
        this value to a number larger than one is essential when using many
        threads. If this pool is non-blocking (``block`` is False), there is
        no upper bound on the number of connections created. However, only
        maxsize connections will be saved for reuse.

    block
        When this is True, prevents more than ``maxsize`` connections being
        used at any given time. When there are no more free connections
        available, a request to create a new connection will block until one
        is available. This can be used to effectively throttle the number of
        simultaneous requests made to a single host.
    """
    def __init__(timeout=None, max=10, block=False):
        _log.debug("Creating new http pool")
        self.timeout = timeout
        self.pool = Queue(max)
        self.block = block

        self.num_connections = 0
        # prefill the pool with connections
        [ self.pool.put(self.new()) for i in xrange(max) ]

    def get(self):
        """
        Returns a new connection, if the pool is blocking, this method will
        block until a new connection is made available.
        """
        conn = None
        try:
            conn = self.pool.get(block=self.block)
        except Empty, e:
            conn = self.new()

        return conn

    def put(self, conn):
        """
        Places an existing connection back into the pool. If the pool is full,
        the connection will not be saved.
        """
        try:
            self.pool.put(conn, block=False) # block=False is essential to get a Full notice
        except Full, e:
            _poollog.warning("Discarding connection %i to %s", self.num_connections, self.host)
            self.num_connections -= 1
            
    def new(self):
        """
        Creates a new connection
        """
        self.num_connections += 1
        _poollog.info("Creating connection %i to host %s", self.num_connections, self.host)
        return httplib2.Http(timeout=self.timeout)
    
