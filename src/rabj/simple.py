import logging
import rabj.api as api

RABJ_PROD = "http://data.labs.freebase.com/"
RABJ_TEST = "http://dw01.corp.metaweb.com/"

_log = logging.getLogger('pyrabj.simple')

class RabjServer(object):
    def __init__(self, server):
        """Create a new reference to a rabj server."""
        if server.endswith('/rabj/store/'):
            self.server = server[:-11]
        elif server.endswith('/rabj/'):
            self.server = server[:-5]
        else:
            self.server = server
        
            self.store = api.RabjCallable(self.server).rabj.store

    def _norm_qid(self, qid):
        if qid.startswith('/rabj/store'):
            return qid[11:]
        elif qid.startswith('/store'):
            return qid[6:]
        else:
            return qid
        
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
        return RabjQueue(queue)

    def get_queue(self, queue_id, access_key=None):
        """
        Fetch a queue by its id
        """
        resp, result = self.store[self._norm_qid(queue_id)].get(access_key=access_key)
        return RabjQueue(result)
    
    def delete_queue(self, queue_id, access_key=None):
        """
        Delete a queue by id        
        """
        resp, result = self.store[self._norm_qid(queue_id)].delete(access_key=access_key)
        return result
    
    def queues_by_accesskey(self, access_key):
        """
        Fetch a list of queues which may be operated with a given access key
        """
        resp, result = self.store.queues.access_key.get(access_key=access_key)
        return [ RabjQueue(queue) for queue in result ]

    def public_queues(self):
        """
        Fetch a list of public queues
        """
        resp, result = self.store.queues.public.get()
        return [ RabjQueue(queue) for queue in result ]
    
    def queues_by_tags(self, tags, access_key=None):
        """
        Fetch a list of queues which have the given tags. Optionally include
        an access key to authorize access to the queues
        """
        if isinstance(tags, basestring):
            tags = [tags]
        resp, result = self.store.queues.tags.get(tag=tags, access_key=access_key)
        return [ RabjQueue(queue) for queue in result ]
    
    def queues_by_owner(self, owner):
        """
        Fetch a list of queues by owner
        """
        resp, result = self.store.queues.owner.get(owner=owner)
        return [ RabjQueue(queue) for queue in result ]
    
class RabjQueue(object):
    """
    A wrapper class around a rabj queue, provides convenience methods for
    introspecting the state of a queue
    """
    def __init__(self, queue=None, server=None, id=None, access_key=None):
        """
        Create a new rabj queue. Not intended to be used directly, see the
        queue creation and fetching methods in RabjServer
        """
        assert (queue!=None) ^ ((server!=None) & (id!=None) & (access_key!=None))

        if not queue:
            queue = api.RabjCallable(server, access_key=access_key)[id].get()         
        self.queue = queue
        self._status_fetched = False
        self._status = None

    def __repr__(self):
        return repr(self.queue)

    def __str__(self):
        return str(self.queue)

    def __getitem__(self, key):
        return self.queue[key]

    def get(self, key, **kwargs):
        return self.queue.get(key, **kwargs)
    
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
        Add a list of questions passed as a list of three-tuples (assertion,
        answerspace, metadata dict), optionally provide a batchsize, default
        of 1000
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

        return added

    def delete(self, questions):
        """
        Delete a set of questions from a queue
        """
        resp, result = self.queue.questions.delete(questions=[q['id'] for q in questions])
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
    
    def status(self):
        resp, result = self.queue.status.get()
        qstat = result['status']
        simple_status = { "judgments": qstat.get('judgments', 0),
                          "complete": qstat.get('complete', 0),
                          "incomplete": qstat.get('wanting', 0),
                          "started": qstat.get('started', 0),
                        }
        
        simple_status["questions"] = (simple_status["complete"] +
                                      simple_status["incomplete"])
        return simple_status

    def all_questions(self):
        resp, result = self.queue.questions.get()
        fetched = [ q.get() for q in result['questions'] ]
        return [ RabjQuestion(res) for (r, res) in fetched ]

    def completed_questions(self):
        resp, result = self.queue.questions.complete.get()
        fetched = [ q.get() for q in result['questions'] ]
        return [ RabjQuestion(res) for (r, res) in fetched ]

    def incomplete_questions(self):
        resp, result = self.queue.questions.incomplete.get()
        fetched = [ q.get() for q in result['questions'] ]
        return [ RabjQuestion(res) for (r, res) in fetched ]
    

class RabjQuestion(object):
    """
    A wrapper class around a rabj question, provides convenience methods for
    introspecting the state of the question
    """
    def __init__(self, question=None, server=None, id=None):
        assert (question!=None) ^ ((server!=None) & (id!=None))

        if not question:
            question = api.RabjCallable(server)[id].get()
        self.question = question

    def __repr__(self):
        return repr(self.question)

    def __str__(self):
        return str(self.question)

    def __getitem__(self, key):
        return self.question[key]

    def get(self, key, **kwargs):
        return self.question.get(key, **kwargs)
    
    def judgments(self):
        resp, result = self.question.judgments.get()
        return result['judgments']
    
