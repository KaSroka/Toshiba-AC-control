#!/usr/bin/env python

from distutils.core import setup

setup(name='toshiba-ac',
      version='0.1',
      description='Toshiba AC controller',
      author='Kamil Sroka',
      author_email='kamilsroka92@gmail.com',
      packages=['toshiba_ac'],
      install_requires=['azure-iot-device', 'httpx'],
     )
