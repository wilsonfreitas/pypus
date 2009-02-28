#!/usr/bin/env python

from distutils.core import setup

setup(name="pypus",
      version="0.1",
      py_modules=['pypus'],
      author='Wilson Freitas',
      author_email='wilson.freitas@gmail.com',
      description='',
      url='http://aboutwilson.net/pypus',
      license='GPL',
      long_description='''\
''',
      scripts = ['pypus'],
      data_files=[('config', ['pypus.ini'])]
      )
