#!/usr/bin/env python

from setuptools import setup

setup(name='repositorytools',
      description='Repository tools',
      packages=['repositorytools'],
      scripts=['scripts/artifact', 'scripts/repo'],
      platforms='any',
)
