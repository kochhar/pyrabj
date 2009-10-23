'''
setup.py

template script to setup data team packages

author: shailesh kochhar, zenkat
date: Oct 14, 2008

(c) 2008, Metaweb Technologies
'''

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
import glob, os, stat

def executable(path):
    st = os.stat(path)[stat.ST_MODE]
    result = (st & stat.S_IEXEC) and not stat.S_ISDIR(st)
    print path, (result and "is" or "is not"), "executable"
    return result
    
# string defining a glob pattern to find script files
script_file_glob = os.path.join(os.path.dirname(__file__), "scripts", "*")
scripts_list = glob.glob(script_file_glob)

setup(name='pyrabj',
      version='0.1',
      description='Python client for rabj',
      url='https://wiki.metaweb.com/index.php/RABJ/client',
      install_requires=["jsonlib2 == 1.5",
                        "httplib2 == 0.4.0", ],
      package_dir={'': 'src'},
      packages=find_packages(exclude=["ez_setup"]),
      scripts=filter(executable, scripts_list)
)
