mkplugin:
	curl -k https://raw.githubusercontent.com/stardust85/make-plugins/master/make-rpm.mk > make-rpm.mk

-include make-rpm.mk

unittests:
	. venv/bin/activate && nosetests -v --exe tests/unit && deactivate

systemtests:
	. venv/bin/activate && nosetests -v --exe tests/system && deactivate

singletest:
	. venv/bin/activate && nosetests -v --exe $(test) && deactivate

tests:
	. venv/bin/activate && nosetests -v --exe tests/unit tests/system --with-coverage --cover-package=repositorytools && deactivate

venv:
	virtualenv --system-site-packages venv
	venv/bin/pip install -r requirements.txt

docs:
	. venv/bin/activate && sphinx-apidoc -f -o docs repositorytools && deactivate
	. venv/bin/activate && make -C docs html && deactivate

.PHONY: all tests docs