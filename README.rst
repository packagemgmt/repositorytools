.. image:: https://travis-ci.org/stardust85/repositorytools.svg?branch=master
    :target: https://travis-ci.org/stardust85/repositorytools
    :alt: CI Build

Python API and command-line interface for working with Sonatype Nexus
=====================================================================

How to install
--------------

::

    pip install repositorytools

Documentation
-------------

is on `rtfd`_

How to run commands locally
---------------------------

::

    scripts/{artifact,repo}

and if it fails (for example in Vagrant on windows, due to symlink), you
can try:

::

    PYTHONPATH=$PWD scripts/{artifact,repo}

How to run tests locally
------------------------

1. Install pycharm >=3.4.1
2. Install virtualbox and vagrant
3. Tools -> Vagrant -> Up
4. Settings -> Interpretters -> add -> remote -> vagrant
5. Run -> Edit Configurations -> add variables REPOSITORY\_PASSWORD
   (nexus admin password) and REPOSITORY\_URL. The nexus instance has to
   be professional for some tests.
6. Shift F10

.. _rtfd: http://repositorytools.readthedocs.org/en/latest/
