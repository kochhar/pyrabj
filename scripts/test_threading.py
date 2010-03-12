import logging, random, time
import rabj.simple as s

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('theadtest')

def run_fetch(queue, threads):
    log.info("Starting test with %i thread(s)", threads)
    queue.threads = threads
    start = time.time()
    cq = rq.completed_questions(judgments=True)
    stop = time.time()
    log.info("Completed test with %i thread(s), took %0.5fs", threads, stop - start)
    
server = s.RabjServer(s.RABJ_TRUNK)
rq = server.get_queue('/rabj/store/queues/queue_124485627369_0', access_key='')
# fetch once to eliminate memory effects

order = [ 1, 2, 5, 10, 20 ]
random.shuffle(order)
for p in order:
    run_fetch(rq, p)

