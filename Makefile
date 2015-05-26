NOSEOPTIONS = -x -v --exe

mkplugin:
	curl -k https://raw.githubusercontent.com/stardust85/make-plugins/master/make-rpm.mk > make-rpm.mk

-include make-rpm.mk

unittests:
	. venv/bin/activate && nosetests $(NOSEOPTIONS) tests/unit && deactivate

systemtests:
	. venv/bin/activate && nosetests $(NOSEOPTIONS) tests/system && deactivate

singletest:
	. venv/bin/activate && nosetests $(NOSEOPTIONS) $(test) && deactivate
	# example: make singletest test=tests/system/repository_test.py:RepositoryTest.test_set_artifact_metadata

tests:
	. venv/bin/activate && nosetests $(NOSEOPTIONS) tests/unit tests/system --with-coverage --cover-package=repositorytools && deactivate

venv:
	virtualenv --system-site-packages venv
	venv/bin/pip install -r requirements.txt

docs:
	. venv/bin/activate && sphinx-apidoc -f -o docs repositorytools && deactivate
	. venv/bin/activate && make -C docs html && deactivate

.PHONY: tests docs