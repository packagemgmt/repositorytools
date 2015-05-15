#!/usr/bin/env python

from setuptools import setup

setup(name='repositorytools',
      description='Tools for working with artifact repositories',
      author='Michel Samia',
      author_email='stardust1985@gmail.com',
      url='https://github.com/stardust85/repositorytools',
      license='Apache 2.0',
      platforms='any',

      classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Environment :: Console',
      ),

      packages=['repositorytools'],
      scripts=['scripts/artifact', 'scripts/repo'],
)
