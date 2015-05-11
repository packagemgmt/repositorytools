Python API and command-line interface for working with Sonatype Nexus
=====================================================================

Documentation
-------------
is on [rtfd](http://repositorytools.readthedocs.org/en/latest/)

How to run commands locally
---------------------------
```
scripts/{artifact,repo}
```

and if it fails (for example in Vagrant on windows, due to symlink), you can try:
```
PYTHONPATH=$PWD scripts/{artifact,repo}
```

How to run tests locally
------------------------

1. Install pycharm >=3.4.1
1. Install virtualbox and vagrant
1. Tools -> Vagrant -> Up
1. Settings -> Interpretters -> add -> remote -> vagrant
1. Run -> Edit Configurations -> add variables REPOSITORY_PASSWORD (nexus admin password) and REPOSITORY_URL.
   The nexus instance has to be professional for some tests.
1. Shift F10