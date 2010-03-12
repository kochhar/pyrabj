import sys
import rabj.simple as s

def export(start=0, num=None):
    if num == 0:
        return

    srv = s.RabjServer(s.RABJ_PROD)
    queues = srv.queues_by_tags(['typewriter'], access_key='rabjrootaccesskey_09302009')
    tq = queues[0]
    assert tq['name'] == "Typewriter"
    assert tq['owner'] == "/user/alexander"

    batch = 5000
    exported = 0

    while True:
        limit = min(batch, num-exported)
        offset = start+exported
        sys.stderr.write("Exporting from index %i\n" %(offset, ))
        resp, result = tq.queue.questions.complete.get(body=True, judgments=True, limit=limit, offset=offset)

        for q in result['questions']:
            sys.stdout.write(q.tojson())
            sys.stdout.write("\n")
        sys.stdout.flush()

        if len(result) < limit:
            break
        
        exported += len(result)
        if num and exported >= num:
            break

    
def main(opts, args):
    export(opts.start, opts.num)

    return 0
    
if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-n", "--number", action="store", dest="num", type=int,
                      help="The number of questions to export")

    parser.add_option("-s", "--start", action="store", dest="start", type=int, default=0,
                      help="The starting point from where to export")
                      
    opts, args = parser.parse_args()
    sys.exit(main(opts, args))
    
