'''
__init__.py

placeholder for rabj module

@author: kochhar
@data Jun 2, 2009

(c) Metaweb Technologies, 2009
'''
VERSION = 0.1

import logging
import util as u, containers as c

# add a default null handler to the logger to turn off warning messages
_log = logging.getLogger('pyrabj')
_log.addHandler(u.NullHandler())
