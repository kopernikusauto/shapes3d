#!/usr/bin/env python

from setuptools import find_packages
from setuptools import setup

setup(name='shapes3d',
      version='0.1',
      description='Shapes3D environment v2.0',
      author='Mike Woodcock',
      author_email='mike@kopernikusauto.com',
      url='https://www.kopernikusauto.com/',
      packages=find_packages('src'),
      package_dir={'':'src'}
     )
