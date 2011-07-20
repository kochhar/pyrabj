#!/usr/bin/env python

import rabj.simple as s
srv = s.RabjServer('http://rabj.freebase.com')
pqs = srv.public_queues()
print type(pqs[0].queue)
