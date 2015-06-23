.. image:: https://travis-ci.org/stardust85/repositorytools.svg?branch=master
    :target: https://travis-ci.org/stardust85/repositorytools
    :alt: CI Build

Python API and command-line interface for working with Sonatype Nexus
=====================================================================

How to install
--------------

::

    pip install repositorytools

Some command line examples
--------------------------
for more commands run repo -h and artifact -h
::

    export REPOSITORY_URL=http://repo.example.com
    export REPOSITORY_USER=admin
    export REPOSITORY_PASSWORD=mysecretpassword

    artifact upload foo-1.2.3.ext releases com.fooware
    artifact resolve com.fooware:foo:latest

Some library examples
---------------------
::

    import repositorytools

    artifact = repositorytools.RemoteArtifact.from_repo_id_and_coordinates('test', 'com.fooware:foo:1.2.3')
    client = repositorytools.repository_client_factory()
    client.resolve_artifact(artifact)
    print(artifact.url)

Documentation
-------------

is on http://repositorytools.readthedocs.org/en/latest/

