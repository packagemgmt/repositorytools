How to run commands locally
---------------------------

Activate the virtualenv and run the script

::

    {artifact,repo}


How to run tests locally
------------------------

Activate the virtualenv, go into the project directory and run:

::

    nosetests -v

Alternatively:

1. Install pycharm >=3.4.1
2. Install virtualbox and vagrant
3. Tools -> Vagrant -> Up
4. Settings -> Interpretters -> add -> remote -> vagrant
5. Run -> Edit Configurations -> add variables REPOSITORY\_PASSWORD
   (nexus admin password) and REPOSITORY\_URL. The nexus instance has to
   be professional for some tests.
6. Shift F10

.. _rtfd: http://repositorytools.readthedocs.org/en/latest/
