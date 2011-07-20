"""
__init__.py

Placeholder for the jycompat module, provides compatability for 2.6
code in Jython 2.5
"""
import platform

if not platform.system().lower().startswith('java'):
  raise RuntimeError("Trying to import the jycompat module when not running "
                     "Jython. System platform is %s" % (platform.system(), ))
