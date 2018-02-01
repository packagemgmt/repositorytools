NOSEOPTIONS = -x -v --exe --nologcapture
VENV_HOME?=.

mkplugin:
	curl -k https://raw.githubusercontent.com/stardust85/make-plugins/master/make-rpm.mk > make-rpm.mk

-include make-rpm.mk

testrelease:
	sed -i "s/'.*'/'$(VERSION)'/" repositorytools/__init__.py
	git commit -a -m 'bumped version'
	git push
	git tag $(VERSION)
	git push --tags
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine upload -r pypitest
release:
	twine upload -r pypi

unittests:
	. $(VENV_HOME)/testenv/bin/activate && nosetests $(NOSEOPTIONS) tests/unit && deactivate

systemtests:
	. $(VENV_HOME)/testenv/bin/activate && nosetests $(NOSEOPTIONS) tests/system && deactivate

singletest:
	. $(VENV_HOME)/testenv/bin/activate && nosetests $(NOSEOPTIONS) $(test) && deactivate
	# example: make singletest test=tests/system/repository_test.py:RepositoryTest.test_set_artifact_metadata

tests: testenv
	. $(VENV_HOME)/testenv/bin/activate && nosetests $(NOSEOPTIONS) tests/unit tests/system --with-coverage --cover-package=repositorytools && deactivate

testenv:
	virtualenv --system-site-packages $(VENV_HOME)/testenv
	$(VENV_HOME)/testenv/bin/pip install -U pip
	$(VENV_HOME)/testenv/bin/pip install --ignore-installed -e .
	$(VENV_HOME)/testenv/bin/pip install -r requirements.txt

docs:
	. venv/bin/activate && sphinx-apidoc -f -o docs repositorytools && deactivate
	. venv/bin/activate && make -C docs html && deactivate

.PHONY: tests docs
