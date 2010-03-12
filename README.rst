Pyrabj is a library which provides access to the RABJ service from
Metatweb. For more information about RABJ see http://rabj.freebaseapps.com

Requirements
============

This library and its dependencies require:

 * jsonlib2 
 * httplib2 0.4.0+
 * Python 2.6+.
 
Installation
============

The easiest way to get pyrabj is if you have easy_install available::

	easy_install http://github.com/kochhar/pyrabj/tarball/master

This will install the latest version of pyrabj. Without easy_install,
download the source from from `Github
<http://github.com/kochhar/pyrabj/archives/master>`_, unpack the downloaded
archive and run::

	python setup.py install

The current `development version
<http://github.com/kochhar/pyrabj/tarball/master#egg=pyrabj-dev>`_ can be
added to your setuptools enabled package by adding::

    install_requires = [ "pyrabj >=0.0, == dev" ]

to your setup.py file.

