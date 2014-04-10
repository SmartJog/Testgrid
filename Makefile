# copyright (c) 2013-2014 smartjog, released under the GPL license.

.PHONY: usage install clean test ci

MODULES := strfmt.py docopt.py vagrant.py bottle.py
SOURCES :=\
	client.py debian.py local.py main.py model.py parser.py persistent.py\
	playground.py remote.py rest.py test.py testbox.py

usage:
	@echo "Usage:"
	@echo "  make install  install testgrid command line tool and framework"
	@echo
	@echo "Reserved:"
	@echo "  make clean    delete generated files"
	@echo "  make test     run tests"
	@echo "  make ci       check-in changes below"
	@echo
	@echo "Changes:"
	@git status -s

testgrid/%.py: ~/Documents/work/%.py
	cp -p $< $@

ifeq ($(shell uname -s), Darwin)
install:
	easy_install pip
	CFLAGS=-Qunused-arguments CPPFLAGS=-Qunused-arguments pip install ansible
	python setup.py install
else
ifeq ($(shell uname -s), Linux) # FIXME (Debian/Ubuntu only)
install:
	apt-get install -qqy python-setuptools
	apt-get install python-pip
	pip install ansible
	python setup.py install
else
$(error unsupported platform)
endif
endif

clean:
	-rm -rf build dist testgrid.egg-info
	-find . -name '*.pyc' -delete

ifneq ($(which testy),)
test: NAME :=
test: $(addprefix testgrid/,$(MODULES))
	testy -m test.ini $(NAME)
else
test:
	@echo please install git@git.smartjog.net:florent.claerhout/testy.git
endif

ci:
	git commit -a
	git push
	git push --tags
