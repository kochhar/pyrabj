import random, os
import rabj.simple as s

userid = os.environ.get('LOGNAME', os.getlogin())

def create_or_find_bogus_queue(name, owner, passwd):
    server = s.RabjServer(s.RABJ_PROD)

    queue_tags = ["tutorial", "bogus", owner]
    myqueues = server.queues_by_tags(queue_tags, access_key=passwd)

    if len(myqueues) == 0:
        myqueue = server.create_queue(name, owner, 1, passwd, queue_tags)
    elif len(myqueues) == 1:    
        myqueue = myqueues[0]
    else:
        myqueue = myqueues[0]
        resp, result = server.store.queues.tags.get(tag=queue_tags, access_key=passwd)
        print "WARNING: Found more than one queue with tags: %s. See %s" % (queue_tags, resp.url)
    
    return myqueue

def create_bogus_questions(queue):
    added = queue.addall( [ (["hands all over", "soundgarden" ],
                             [ "yes", "no"],
                             { "tags": ["bogus"] }
                           ),
                           ( ["pyrabj", "scripts"],
                             ["yes", "no"],
                             { "tags": ["bogus"] }
                           ),
                           ( ["sweet jane", "lou reed"],
                             ["yes", "no"],
                             { "tags": ["bogus"] }
                           ),
                           ( ["rabj trunk", "rabj prod" ],
                             [ "yes", "no"],
                             {"tags": [ "bogus" ]}
                           ),
                           ( ["my last mistake", "dan auerbach"],
                             [ "yes", "no"],
                             {"tags": [ "bogus"]}
                           )

                          ])
    return added

def create_questions(queue):
    randints = [ (random.randint(0, 1000), random.randint(0, 1000)) for i in range(5) ]
    toadd = [ ([r1, "<", r2], ["yes", "no"], {}) for (r1, r2) in randints ]
    added = queue.addall(toadd)
    return added

if __name__ == "__main__":
    from sys import stdin, stdout

    stdout.write("Give a name to your queue [default: tutorial-bogus-%(owner)s]: " % {"owner": userid})
    stdout.flush()
    strname = stdin.readline()
    if len(strname.strip()):
        name = strname.strip()
    else:
        name = "tutorial-bogus-%(owner)s"

    stdout.write("The freebase user who owns this queue [default: %(owner)s]: " % {"owner": userid})
    stdout.flush()

    strowner = stdin.readline()
    if len(strowner.strip()):
        owner = strowner.strip()
    else:
        owner = "/user/%(owner)s"

    stdout.write("Enter the access key for your queue [default: tutorial]: ")
    stdout.flush()
    
    strpasswd = stdin.readline()
    if len(strpasswd.strip()):
        passwd = strpasswd.strip()
    else:
        passwd = "tutorial"
    
    name = name % {"owner": userid}
    owner = owner % {"owner": userid}

    queue = create_or_find_bogus_queue(name, owner, passwd)
    print "Created queue %s with tags %s and access key %s" % (queue['id'], queue['tags'], passwd)
    legit = create_questions(queue)
    bogus = create_bogus_questions(queue)
    print "Sent %i questions to queue, %i added, %i existed" % (len(legit) + len(bogus),
                                                                len([q for q in legit + bogus if q['add'] == 'created']),
                                                                len([q for q in legit + bogus if q['add'] == 'exists']))

    print "Queue %s has %i questions" % (queue['id'], queue.questions)
    
    print "Legit questions: "
    for q in legit:
        print q['id']          

    print "Bogus questions: "
    for q in bogus:
        print q['id']
    
