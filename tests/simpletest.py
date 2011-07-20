#!/usr/bin/env python

import rabj.simple as s
srv = s.RabjServer(s.RABJ_PROD)
pqs = srv.queues_by_tags(['matchmaker2'], access_key='rabjrootaccesskey_09302009')
myq = pqs[3]
qques = myq.get_one()
print qques.get_state(myq['id'])
print qques.judgments()
