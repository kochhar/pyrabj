'''
__init__.py

placeholder for rabj module

@author: kochhar
@data Jun 2, 2009

(c) Metaweb Technologies, 2009
'''
import logging, sys
import util as u

"""
The pyrabj version
"""
VERSION = '0.1'
app_name = sys.argv[0] if sys.argv[0] else '__main__'

"""
The current application, used when creating a meaningful User-agent for http requests
"""
APP = app_name.replace('\\', '/')

# add a default null handler to the logger to turn off warning messages
_log = logging.getLogger('pyrabj')
_log.addHandler(u.NullHandler())

import simple as simple
labsrv = simple.RabjServer(simple.RABJ_PROD)
trunksrv = simple.RabjServer(simple.RABJ_TRUNK)

