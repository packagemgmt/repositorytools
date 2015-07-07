.. image:: https://travis-ci.org/stardust85/repositorytools.svg?branch=master
    :target: https://travis-ci.org/stardust85/repositorytools
    :alt: CI Build

.. image:: https://img.shields.io/gratipay/stardust85.svg
    :target: https://gratipay.com/~stardust85/
    :alt: Fundraising

Python API and command-line interface for working with Sonatype Nexus
=====================================================================

How to install
--------------

::

    pip install repositorytools

Some command line examples
--------------------------

Preparing env. variables
~~~~~~~~~~~~~~~~~~~~~~~~
::

    export REPOSITORY_URL=https://repo.example.com
    export REPOSITORY_USER=admin
    export REPOSITORY_PASSWORD=mysecretpassword

Uploading an artifact
~~~~~~~~~~~~~~~~~~~~~
::

    artifact upload foo-1.2.3.ext releases com.fooware

Resolving artifact's URL
~~~~~~~~~~~~~~~~~~~~~~~~
::

    artifact resolve com.fooware:foo:latest

Deleting artifacts
~~~~~~~~~~~~~~~~~~
::

    # by url
    artifact delete https://repo.example.com/content/repositories/releases/com/fooware/foo/1.2.3/foo-1.2.3.ext

    # by coordinates
    artifact resolve com.fooware:foo:latest | xargs artifact delete

Working with staging repositories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Nexus Professional only

::

    repo create -h
    repo close -h
    repo release -h
    repo drop -h
    repo list -h

Working with custom maven metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Nexus Professional only

::

    artifact get-metadata -h
    artifact set-metadata -h



Some library examples
---------------------
For most of methods the same env. variables as above have to be exported or specified in call of repository_client_factory()

Uploading artifacts
~~~~~~~~~~~~~~~~~~~
::

    import repositorytools

    artifact = repositorytools.LocalArtifact(local_path='~/foo-1.2.3.jar', group='com.fooware')
    client = repositorytools.repository_client_factory(user='admin', password='myS3cr3tPasswOrd')
    remote_artifacts = client.upload_artifacts(local_artifacts=[artifact], repo_id='releases')
    print(remote_artifacts)

Resolving artifacts
~~~~~~~~~~~~~~~~~~~
Works even without authentication.
::

    import repositorytools

    artifact = repositorytools.RemoteArtifact.from_repo_id_and_coordinates('test', 'com.fooware:foo:1.2.3')
    client = repositorytools.repository_client_factory()
    client.resolve_artifact(artifact)
    print(artifact.url)

Deleting artifacts
~~~~~~~~~~~~~~~~~~~

::

    import repositorytools

    artifact = repositorytools.RemoteArtifact.from_repo_id_and_coordinates('test', 'com.fooware:foo:1.2.3')
    client = repositorytools.repository_client_factory(user='admin', password='myS3cr3tPasswOrd')
    client.resolve_artifact(artifact)
    client.delete_artifact(artifact.url)


Documentation
-------------

is on http://repositorytools.readthedocs.org/en/latest/

Support
-------
You can support my effort many ways:
 * create issues
 * fix issues (by sending pull requests)
 * donating on https://gratipay.com/~stardust85/, you can send even 1 cent per month ;) (but the more the better)