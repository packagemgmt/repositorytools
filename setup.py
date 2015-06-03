#!/usr/bin/env python

from setuptools import setup, find_packages
import re

version = ''
with open('repositorytools/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

setup(name='repositorytools',
      version=version,
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

      packages=find_packages(),
      scripts=['scripts/artifact', 'scripts/repo'],
      download_url='https://github.com/stardust85/repositorytools/tarball/3.0.52'
)
