.. highlight:: python
   :linenothreshold: 5


PyRABJ Tutorial
===============

PyRABJ is a Python library written to manage RABJ queues, questions and
answers from the command line or from other Python programs. This is useful,
for example, to populate a queue with questions, to retrieve all the answers
to a question and to automate operations which would be tedious and error
prone when using the `RABJ Explorer <http://rabj.freebaseapps.com/ RABJ
Explorer>`_. The code for pyrabj is open-sourced and is available on GitHub
at http://github.com/kochhar/pyrabj.

This is a short guide to using the pyrabj client for typical RABJ tasks. For
a detailed look at the API and a complete description of the methods
supported see `the complete RABJ api
<http://wiki.freebase.com/wiki/RABJ_API>`_.

Getting started: Installation
=============================
pyrabj is setuptools compatible. The simplest way to get started is to
install it into your python distribution using
``easy_install``. Alternatively, you could take a slightly more involved
route and checkout the source from github and run the setup script. The
latter allows you to track changes to pyrabj yourself, while the first gives
you access to the latest and greatest version.

NOTE: pyrabj needs Python 2.6 or better

Using easy_install
------------------
To install the latest development version of pyrabj, point ``easy_install``
to the head of the git repository::

 % easy_install http://github.com/kochhar/pyrabj/tarball/master

Checkout from github
--------------------
This method assumes that you are familiar with using `github
<http://www.github.com/>`_ to fork and manage source trees. If not please
see the help section on `forking <http://help.github.com/forking/>`_. Once
the source has been fetched (and unpacked if necessary), use the following::

 % cd pyrab_dir_from_git
 % python setup.py install

Getting started: Testing that it works
======================================

Once you have got the pyrabj package setup, you should test it out in your
interpreter::

 % python
 >>> import rabj

The import should succeed without any problems.

Getting started: Using pyrabj
=============================
To use pyrabj, fire up your interpreter, import the :mod:`rabj.simple` module and
create a reference to the rabj server::

 % python
 >>> import rabj.simple as simple
 >>> server = simple.RabjServer(simple.RABJ_PROD)

The server reference will allow you to query RABJ for queues and questions
which might reside on the server.

Create queues and questions
-----------------------------
In this section we cover how to create new queues and add questions to them.

Create a new queue
^^^^^^^^^^^^^^^^^^
Creating a new queue requires a few key fields, a name, the owner of the
queue, a key to access questions and the number of votes required per
question::

 >>> queue = server.create_queue(name="RABJ Sample queue",
                                 owner="/user/kochhar",
                                 votes=1,
                                 access_key="samplekey",
                                 tags=["sample"])
 >>> print queue

The returned object is a :class:`~rabj.simple.RabjQueue` instance. It behaves much like a
dictionary, with some additional methods to query the state of the queue on
the server. 

The newly created queue should have an ``id`` field which looks something like
``'/rabj/store/queues/queue_XXXXXXXXXX_0'``. This is a unique identifier for the
queue and can always be used to retrieve the queue from the RABJ server.

Fetch a queue by id
^^^^^^^^^^^^^^^^^^^
Once a queue has been created, you can fetch another instance of the queue
by using its id::

  >>> queue_copy = server.queue_by_id(queue_id=queue['id'])
  >>> print queue_copy


Find a queue by access key
^^^^^^^^^^^^^^^^^^^^^^^^^^
Once a queue has been created, it can also be retrieved by its access key::

 >>> queues = server.queues_by_accesskey(access_key="samplekey")
 >>> for q in queues:
 ...     print q


Find a queue by tag
^^^^^^^^^^^^^^^^^^^
The other alternative to discover queues is to fetch queues which have a
tag. This method requires both a tag and an access key, it will only return
the queues for which the access key is valid::

 >>> queues = server.queues_by_tags(tags=["sample"],
                                    access_key=None)
 >>> for q in queues
 ...     print q

Add a question to a queue
^^^^^^^^^^^^^^^^^^^^^^^^^
Once a queue has been created, you're free to add questions to it. The
example below adds a single question to the queue. 

There are two required fields, the assertion and the answerspace. The
assertion is used to uniquely identify a question while the answerspace
provides a simple way to enumerate the possible set of responses for a
question.

Additionally, you can add other fields into the question which will be
stored along with the assertion and the answerspace::

 >>> myqueue = queues[0]
 >>> add = myqueue.addone(assertion=[ "/topic/1", "similar", "/topic/2"],
                          answerspace=["yes", "no", "maybe", "skip"],
                          foo_field="foo_value",
                          bar_field="bar_value)")
 >>> print add
 
Add questions to a queue from a file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This assumes that the lines in the file are json encoded as lists of size 3
(assertion, answerspace, metadata-dict)::

 >>> import jsonlib2
 >>> myqueue = queues[0]
 >>> question_list = []
 >>> for line in open('question_file.json')
 ...     assertion, answerspace, meta = jsonlib2.loads(line)
 ...     question_list.append((assertion, answerspace, meta))
 >>> added = myqueue.addall(question_list)
 >>> print added

Examine the state of a queue
----------------------------
In the course of normal operation, there will be instances when you need to
find out the state of a queue. The :class:`~rabj.simple.RabjQueue` instance 
provides some helper methods to interrogate the RABJ servers about the state
of a queue.

Check status
^^^^^^^^^^^^
The status method provides a unified view of the queue status::

  >>> status = myqueue.status()
  >>> print status

Counting
^^^^^^^^
All questions::

  >>> print myqueue.questions

Completed questions::

  >>> print myqueue.complete

Incomplete questions::

  >>> print myqueue.incomplete

Judgments::

  >>> print myqueue.judgments

Retrieve existing objects
-------------------------
Fetch all questions on a queue
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

 >>> questions = myqueue.all_questions()
 >>> for q in questions:
 ...     print q['id']

Fetch completed questions
^^^^^^^^^^^^^^^^^^^^^^^^^
::

 >>> questions = myqueue.completed_questions()
 >>> for q in questions:
 ...     print q['id']

Fetch questions completed after some point in time
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This example fetches questions which have been completed after Aug, 24 2009
08:00:00::

  >>> questions = myqueue.completed_questions(since='2009-08-24 08:00:00')
  >>> for q in questions:
  ...     print q['id']

Fetch completed questions with judgments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  >>> completed_w_judgments = myqueue.completed_questions(judgments=True)
  >>> for ques in completed_w_judgments:
  ...     print ques


Updating objects
----------------
Of course, you will need to change things from time to time. Perhaps modify
some questions to add tags, or to change the number of votes. 

Updating queue tags
^^^^^^^^^^^^^^^^^^^
Let's add a tag to our queue::

  >>> myqueue = ...
  >>> myqueue['tags'].append('tutorial2')
  >>> myqueue.update()
  >>> print myqueue['tags']

You should see ``'tutorial2'`` in the list of tags.


Updating question tags
^^^^^^^^^^^^^^^^^^^^^^
This example shows how to add tags to some questions. Let's update questions
that have been tagged as ``people`` to be tagged as ``type:/people/person``
instead::

  >>> myqueue = ...
  >>> allquestions = myqueue.all_questions()
  >>> for q in allquestions:
  ...     if 'people' in q['tags']:
  ...         q['tags'].remove('people')
  ...         q['tags'].append('type:/people/person')
              q.update()

Changing question votes
^^^^^^^^^^^^^^^^^^^^^^^
For this part, we will increase the number of votes required for all
completed questions by 2 if it has received more than two ``skip`` votes::

  >>> myqueue = ...
  >>> completed_questions = myqueue.completed_questions(judgments=True)
  >>> queueid = myqueue['id']  # use this later
  >>> for q in completed_questions:
  ...     judgments = q['judgments']
  ...     if len([ j for j in judgments if j['value'] == 'skip' ]) > 2:
  ...         q['votes'] = myqueue['votes'] + 2
  ...         q.update()
  ...         # change the state of the question, this is tricky
  ...         q.question.state[qeueueid].post(state='wanting')
  
There are a few points to note in this snippet. First, in Line 2, we pass
``judgments=True`` when fetching the completed questions from the
queue. This saves additional round trips later. Next, in Line 8, we update
the question after setting the votes. 

Finally, in Line 10, we change the state of the question to wanting
i.e. we make it available again. This bit has a lot going on so let's take a
closer look::

  ...         q.question.state[qeueueid].post(state='wanting')

First, we are accessing the ``question`` attribute from ``q``. But ``q`` was
returned as a completed question. What's going on? Well take a look at the
type of ``q``:: 

  >>> q = completed_questions[0] 
  >>> type(q) 
  <class 'rabj.simple.RabjQuestion'>

:class:`rabj.simple.RabjQuestion` is a python class which provides some
convenience methods on top of the lower level classes in :mod:`rabj.api`. In
this case, ``RabjQuestion`` is a a wrapper on top of
:class:`rabj.api.RabjCallable`. There's more to say about ``RabjCallable``,
but the short version is that is translates python attributes to
url-components and allows making http method calls to those urls. For more
details see the documentation for :class:`rabj.api.RabjCallable`.

In this case we're using the ``RabjCallable`` to access urls which don't
have methods in ``rabj.simple``. It was meant to be simple right?::

  >>> rc = q.question.state[queueid]
  >>> print rc._url
  http://rabj.trunk.metaweb.com/rabj/store/questions/question_c4c08f3d44a26a1d/state/rabj/store/queues/queue_1256677903328_0/
  
That's the url we're going to post to. And when we post, we'll include a body
which says that the state is ``wanting``. 

Take another look, you should see it clearly now::
  
  ...         q.question.state[qeueueid].post(state='wanting')


Delete Existing Objects
-----------------------
There will be times when you need to delete existing objects. Please note
that deleting queues does not delete questions. Questions **MUST** be
deleted separately. 

Deleting questions from a queue
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This example will walk you through deleting the questions on a queue which
have been flagged as "bogus".

Here we're guessing that you have created a queue like ours. If you try this
example, you can use the :download:`example script
</tutorial_bogus_queue.py>` to create a new queue. The script is also
available from `our source repository
<http://github.com/kochhar/pyrabj/tree/master/scripts/>`_.

::

  >>> myqueue = ...  
  >>> allquestions = myqueue.all_questions()
  >>> toremove = list()
  >>> for q in allquestions:
  ...     if "bogus" in q['tags']:
  ...         toremove.append(q)
  ...
  >>> myqueue.delete(questions=toremove)
  >>> for q in toremove:
  ...     q.delete()
  ...
  

Note how we first delete the questions from the queue on line 8 and then
delete the questions in line 10. The order of these operations is important.
If the questions are deleted first, the queue would reference deleted
questions.

Delete all questions from a queue
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
There's a convenient method for deleting all the questions on a queue at once
::

 >>> delete = myqueue.deleteall()
 >>> print delete

Delete an entire queue
^^^^^^^^^^^^^^^^^^^^^^
In order to delete a queue you must ask the server. As always, an access
key will be required.
::

 >>> queue_delete = myserver.delete(queue=myqueue, access_key=myaccesskey)
 >>> print queue_delete

The ``queue`` parameter can be a string id or a RabjQueue instance. 
