1. check that file `` ~/.pypirc`` exists and contains correct credentials. For more info please see https://docs.python.org/2/distutils/packageindex.html#pypirc
1. commit and push changes if you have some (optional, because you maybe already got some changes from pull requests)
1. run automated tests or look at travis results
1. if your change isn't covered by tests, run a manual test of the change
1. if the tests were ok, run the following command to release it to test pypi
   ```
   make testrelease VERSION=1.2.3  # use the version you want to release it as
   ```
1. you can test it now also by installing it from testpypi
1. release to prod pypi
   ```
   make release
   ```

example of ~/.pypirc:
```
[distutils] # this tells distutils what package indexes you can push to
index-servers =
    pypi
    pypitest

[pypi]
username: packagemgmt
password: *****************

[pypitest]
repository: https://test.pypi.org/legacy/
username: packagemgmt
password: ******************
```
