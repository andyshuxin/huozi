"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup
import os

APP = ['toolsimple.py']
DATA_FILES = []
for files in os.listdir('/Users/andy/Dropbox/huozi/img/'):
    f1 = '/Users/andy/Dropbox/huozi/img/' + files
    if os.path.isfile(f1):
        f2 = 'img', [f1]
        DATA_FILES.append(f2)
OPTIONS = {'arch': 'i386',
           'argv_emulation': True,
           'packages': ['lxml'],}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
