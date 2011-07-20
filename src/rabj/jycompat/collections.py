"""
collections module, only provides some features from python 2.6. this
is solely intended for jython 2.5 compatibility
"""

# For bootstrapping reasons, the collection ABCs are defined in _abcoll.py.
# They should however be considered an integral part of collections.py.
from _abcoll import *
import _abcoll
__all__ = _abcoll.__all__[:]
