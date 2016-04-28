#!/usr/bin/env python
import io
import os
import re
import sys

from setuptools import setup, find_packages

HERE = os.path.dirname(__file__)

with io.open(os.path.join(HERE, 'repositorytools', '__init__.py'), 'rb') as fd:
    found = re.search(br'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE)
    version = found and found.group(1)

if not version:
    raise RuntimeError('Cannot find version information')


install_requires=['requests>=1.1', 'six']

if sys.version_info < (2,7):
    install_requires.append("argparse < 2")

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

setup(name='repositorytools',
      version=version,
      description='Tools for working with artifact repositories',
      long_description=README,
      author='Michel Samia',
      author_email='stardust1985@gmail.com',
      url='https://github.com/stardust85/repositorytools',
      license='Apache 2.0',
      platforms='any',
      install_requires=install_requires,

      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Environment :: Console',
      ],

      packages=find_packages(),
      scripts=['scripts/artifact', 'scripts/repo'],
      download_url='https://github.com/stardust85/repositorytools/tarball/{version}'.format(version=version)
)
