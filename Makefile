# copyright (c) 2013-2014 smartjog, released under the GPL license.

.PHONY: usage install clean test ci

usage:
	@echo "Usage:"
	@echo "  make install  install testgrid command line tool and framework"
	@echo
	@echo "Reserved:"
	@echo "  make clean    delete bytecode"
	@echo "  make test     run test cases validating the implementation"
	@echo "  make ci       check-in code"
	@echo
	@echo "Changes:"
	@git status -s

install:
	apt-get install -qqy python-setuptools
	python setup.py install

clean:
	-rm -rf build dist testgrid.egg-info
	-find . -name '*.pyc' -delete

# install git@git.smartjog.net:florent.claerhout/testy.git first
test:
	testy -m test.ini

ci:
	git commit -a
	git push
