.. image:: https://travis-ci.org/stardust85/repositorytools.svg?branch=master
    :target: https://travis-ci.org/stardust85/repositorytools
    :alt: CI Build

Python API and command-line interface for working with Sonatype Nexus
=====================================================================

How to install
--------------

::

    pip install repositorytools

Some examples
-------------
::

    export REPOSITORY_URL=http://repo.example.com
    export REPOSITORY_USER=admin
    export REPOSITORY_PASSWORD=mysecretpassword

    artifact upload foo-1.2.3.ext releases com.fooware
    # for more commands run repo -h and artifact -h

    artifact resolve com.fooware:foo:latest

Documentation
-------------

is on `rtfd`_

