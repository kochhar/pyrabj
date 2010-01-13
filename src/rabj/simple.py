import logging, Queue, multiprocessing
from rabj import VERSION, APP
import rabj.api as api, rabj.util as u
api._def_headers['User-agent'] = ':'.join([APP, 'pyrabj.simple', VERSION])

"""
Production instance of rabj
"""
RABJ_PROD = "http://data.labs.freebase.com/"
RABJ_TRUNK = "http://rabj.trunk.metaweb.com/"
RABJ_QA = "http://rabj.qa.metaweb.com/"
RABJ_SANDBOX = "http://rabj.sandbox.metaweb.com/"

_log = logging.getLogger('pyrabj.simple')

class RabjServer(object):
    """
    A wrapper class for a rabj server, provides methods for investigating
    queues available on the server.

    server_url
        A url for the rabj server hosting the queue.
    """    
    def __init__(self, server_url, store_path='rabj/store/'):
        """Create a new reference to a rabj server."""
        if server_url.endswith('/rabj/store/'):
            self.server = server_url[:-11]
        elif server_url.endswith('/rabj/'):
            self.server = server_url[:-5]
        else:
            self.server = server_url
        
        self.store = api.RabjCallable(self.server)[store_path]
        self.threads = 1
        
    def create_queue(self, name, owner, votes, access_key, tags=None, **meta):
        """
        Create a new queue giving it a name, owner, a required number of
        votes and optionally including an access_key, tags and any other
        metadata to be associated."""
        votes = int(votes)
        
        if access_key is None:
            _log.warn("You are creating a new queue without providing an access key")
        if tags is None: tags = []

        queue = { "name": name,
                  "owner": owner,
                  "access_key": access_key,
                  "votes": votes,
                  "tags": tags
                }
        queue.update(meta)
        
        resp, queue = self.store.queues.post(queue=queue)
        return RabjQueue(queue, threads=self.threads)

    def get_queue(self, queue_id, access_key=None):
        """
        Fetch a queue by its id
        """
        resp, result = self.store[self._norm_qid(queue_id)].get(access_key=access_key)
        return RabjQueue(result, threads=self.threads)
    
    def delete_queue(self, queue, access_key=None):
        """
        Delete a queue by a string id or a mapping object with an id field.
        """
        if isinstance(queue, RabjQueue) or hasattr(queue, 'get'):
            queue_id = queue['id']
        else:
            queue_id = queue
        
        resp, result = self.store[self._norm_qid(queue_id)].delete(access_key=access_key)
        return result

    def public_queues(self):
        """
        Fetch a list of public queues
        """
        resp, result = self.store.queues.public.get()
        return [ RabjQueue(queue, threads=self.threads) for queue in result ]
    
    # common aliases
    queue_by_id = get_queue
    queues_by_id = get_queue
    
    def queues_by_accesskey(self, access_key):
        """
        Fetch a list of queues which may be operated with a given access key
        """
        resp, result = self.store.queues.access_key.get(access_key=access_key)
        return [ RabjQueue(queue, threads=self.threads) for queue in result ]

    def queues_by_tags(self, tags, access_key=None):
        """
        Fetch a list of queues which have the given tags. Optionally include
        an access key to authorize access to the queues
        """
        if isinstance(tags, basestring):
            tags = [tags]
        resp, result = self.store.queues.tags.get(tag=tags, access_key=access_key)
        return [ RabjQueue(queue, threads=self.threads) for queue in result ]
    
    def queues_by_owner(self, owner):
        """
        Fetch a list of queues by owner
        """
        resp, result = self.store.queues.owner.get(owner=owner)
        return [ RabjQueue(queue, threads=self.threads) for queue in result ]

    queues_by_public = public_queues
    
    def _norm_qid(self, qid):
        if qid.startswith('/rabj/store'):
            return qid[11:]
        elif qid.startswith('/store'):
            return qid[6:]
        else:
            return qid
        

    
class RabjQueue(object):
    """
    A wrapper class around a rabj queue, provides convenience methods for
    introspecting the state of a queue. A rabj queue instance can be created
    either from a :class:`~rabj.api.RabjCallable` object or by providing a server url,
    a queue id and an access_key.

    queue    
        A :class:~rabj.api.RabjCallable which references a queue. Required
        if ``server_url`` and ``id`` are None

    server_url
        A url for the rabj server hosting the queue. Required if queue=None

    id
        The id of the queue on the server. Required if queue=None

    access_key
        The access key for the queue on the server. Required if queue=None
    """
    def __init__(self, queue=None, server_url=None, id=None, access_key=None, threads=1):
        """
        Create a new rabj queue. Not intended to be used directly, see the
        queue creation and fetching methods in RabjServer
        """
        assert (queue!=None) ^ ((server_url!=None) & (id!=None) & (access_key!=None))

        if not queue:
            resp, queue = api.RabjCallable(server_url, access_key=access_key)[id].get()
        
        self.queue = queue
        self.threads = 2 if threads > 1 else 1
        self._status_fetched = False
        self._status = None

    def __repr__(self):
        return repr(self.queue)

    def __str__(self):
        return str(self.queue)

    def __getitem__(self, key):
        return self.queue[key]

    @property
    def parallel(self):
        return True
        
    def update(self):
        """Save modifications to the current queue."""
        resp, result = self.queue.put(queue=self.queue)
        self.queue = result
        return self
    
    def addone(self, assertion, answerspace, **meta):
        """
        Add a single question defined by its assertion, answerspace and any
        other metadata as keyword args.
        """
        question = { 'assertion': assertion,
                     'answerspace': answerspace }
        question.update(meta)
        resp, result = self.queue.questions.post(questions=[question])
        return result['questions']

    def addall(self, three_tuples, pagesize=1000):
        """
        Add questions passed as three-tuples (assertion, answerspace,
        metadata dict), optionally provide a batchsize, default of 1000

        three_tuples:        
            An iterable containing tuples. The first element is treated as
            the assertion, the second as the answerspace and the third as a            
            dictionary containing other metadata.

        pagesize:
            The number of questions to send in one request, default is 1000
        """
        added = []
        payload = []
        for assertion, answerspace, meta in three_tuples:
            question = { 'assertion': assertion,
                         'answerspace': answerspace }
            question.update(meta)
            payload.append(question)
            if len(payload) == pagesize:
                resp, result = self.queue.questions.post(questions=payload)
                added.extend(result['questions'])
                payload = []

        if len(payload):
            resp, result = self.queue.questions.post(questions=payload)
            added.extend(result['questions'])
            payload = []
        
        return added

    def getone(self, question=None):
        """
        Get one question from the queue. Optionally the id of the question to
        fetch can be passed as a parameter.
        """
        if question is not None:
            assert isinstance(question, [basestring, dict])
            if isinstance(question, dict):
                questionid = question['id']
            else:
                questionid = question

            resp, question = self.queue['../../../'][questionid].get()            
        else:
            resp, question = self.queue.questions.get(limit=1)[0]['id']

        return RabjQuestion(question)
        
    def getall(self):
        """
        Get a list of all the question on the queue
        """
        resp, result = self.queue.questions.get()
        fetch = result['questions']
        return [ RabjQuestion(res) for (r, res) in self._get(fetch) ]
        
    def delete(self, questions):
        """
        Delete a set of questions from a queue.

        questions
            An iterable of RabjQuestion objects which should have ids
        """
        resp, result = self.queue.questions.delete(questions=[{'id': q['id']} for q in questions])
        return result

    def deleteall(self):
        """
        Delete all questions from a queue
        """
        questions = self.all_questions()
        return self.delete(questions)
    
    @property
    def questions(self):
        """
        Return the count of questions on the queue
        """
        status = self.statusonce()
        return status["questions"]

    @property
    def complete(self):
        """
        Return the count of completed questions on the queue
        """
        status = self.statusonce()
        return status["complete"]

    @property
    def incomplete(self):
        """
        Return the count of inocomplete questions on the queue
        """
        status = self.statusonce()
        return status["incomplete"]

    @property
    def started(self):
        """
        Return the count of started questions on the queue
        """
        status = self.statusonce()
        return status["started"]

    @property
    def judgments(self):
        """
        Return the count of judgments accumulated for the queue
        """
        status = self.statusonce()
        return status["judgments"]

    def statusonce(self):
        if not self._status_fetched:
            self._status = self.status()
            self._status_fetched = True
        
        return self._status

    def resetstatus(self):
        self._status_fetched = False
        self._status = None
    
    def status(self, **kwargs):
        resp, result = self.queue.status.get(**kwargs)
        qstat = result['status']
        simple_status = { "judgments": qstat.get('judgments', 0),
                          "complete": qstat.get('complete', 0),
                          "incomplete": qstat.get('wanting', 0),
                          "started": qstat.get('started', 0),
                        }
        
        simple_status["questions"] = (simple_status["complete"] +
                                      simple_status["incomplete"])
        return simple_status

    all_questions = getall

    def completed_questions(self, since=None, judgments=False):
        """
        Fetch questions which have been completed. Optionally fetch
        questions completed after a given point in time and include
        judgments also

        since
            Starting point from where to get questions, defaults to all
            questions. Format is YYYY-MM-DD HH:MM:SS

        judgments        
            Include judgments when getting questions, default is False
        """
        params = dict()
        if since:
            params['since'] = since

        resp, result = self.queue.questions.complete.get(**params)
        if judgments == True:
            fetch = [ q.judgments for q in result['questions'] ]
        else:
            fetch = result['questions']
            
        return [ RabjQuestion(res) for (r, res) in self._get(fetch) ]

    def incomplete_questions(self, since=None, judgments=False):
        """
        Fetch questions which have been completed. Optionally fetch
        questions completed after a given point in time and include
        judgments also

        since
            Starting point from where to get questions, defaults to all
            questions. Format is YYYY-MM-DD HH:MM:SS

        judgments        
            Include judgments when getting questions, default is False
        """
        params = {'limit': 0}
        if since:
            params['since'] = since

        resp, result = self.queue.questions.wanting.get(**params)
        if judgments == True:
            fetch = [ q.judgments for q in result['questions'] ]
        else:
            fetch = result['questions']

        return [ RabjQuestion(res) for (r, res) in self._get(fetch) ]

    def _get(self, rabj_callables):
        if self.parallel == True:
            fetched = api.parallel_fetch([ rc.request_params(rc.url, "GET") for rc in rabj_callables ], self.threads)
        else:
            fetched = [ rc.get() for rc in rabj_callables ]

        return fetched

    
class RabjQuestion(object):
    """
    A wrapper class around a rabj question, provides convenience methods for
    introspecting the state of the question
    """
    def __init__(self, question=None, server=None, id=None):
        assert (question!=None) ^ ((server!=None) & (id!=None))

        if not question:
            resp, question = api.RabjCallable(server)[id].get()
            
        self.question = question

    def __repr__(self):
        return repr(self.question)

    def __str__(self):
        return str(self.question)

    def __getitem__(self, key):
        return self.question[key]

    def __setitem__(self, key, value):
        return self.question.__setitem__(key, value)

    def __delitem__(self, key):
        return self.question.__delitem__(key)
    
    def update(self):
        """Saves modifications to the question"""
        resp, result = self.question.put(question=self.question)
        self.question = result
        return self

    def delete(self):
        """Deletes the question from rabj"""
        resp, result = self.question.delete()
        return result
        
    def judgments(self):
        resp, result = self.question.judgments.get()
        return result['judgments']
