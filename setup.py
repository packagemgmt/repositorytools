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

# README.rst file may contains unicode characters, so we use utf8 to read it
with io.open(os.path.join(HERE, 'README.rst'), mode="r", encoding="utf8") as fd:
    long_description = fd.read()

install_requires = ['requests>=2.1', 'six', 'requests-toolbelt']

if sys.version_info < (2, 7):
    install_requires.append("argparse < 2")

setup(
    name='repositorytools',
    version=str(version),
    description='Tools for working with artifact repositories',
    long_description=long_description,
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
