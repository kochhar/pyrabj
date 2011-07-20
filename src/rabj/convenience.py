'''
rabj.convenience

Functions that provide a convenient often used transformation of the
results from a rabj API
'''

import simple


def export_judgments_as_tuples(server, queue, access_key, state, min=2):
  '''
  Exports the judgments from completed questions on a queue.

  The output from this function is an iterable of tuples containing
  (qid, fb_user_id, value)

  If a question has multiple judgments there will be multiple records
  for that questions
  '''
  srv = simple.RabjServer(server)
  queue = srv.get_queue(queue_id=queue, access_key=access_key)

  for q in queue.iterall(state=state, judgments=True):
    if len(q['judgments']) < min:
      continue

    qid = q['id']
    for j in q['judgments']:
      judge = j['user']['fb_user_id']
      jval = j['value']
      if jval == 'reconciled':
        value = "%s:%s" % (j['value'], j['__metadata__']['recon_id'])
      else:
        value = jval

      yield qid, judge, value


def rabj_prod():
  """Returns an instance of RabjServer connected to rabj production"""
  server = simple.RabjServer(simple.RABJ_PROD)
  return server


def rabj_trunk():
  """Returns an instance of RabjServer connected to rabj trunk"""
  server = simple.RabjServer(simple.RABJ_PROD)
  return server
