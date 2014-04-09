# copyright (c) 2013-2014 smartjog, released under the GPL license.

.PHONY: usage install clean test ci

MODULES := strfmt.py docopt.py vagrant.py bottle.py
SOURCES :=\
	client.py debian.py local.py main.py model.py parser.py persistent.py\
	playground.py remote.py rest.py test.py testbox.py

# install git@git.smartjog.net:florent.claerhout/testy.git first
ifeq ($(shell which testy),)
$(warning testy not installed, trying to use sources directly)
TESTY := python ~/Documents/work/testy/main.py
else
TESTY := testy
endif

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

testgrid/%.py: ~/Documents/work/%.py
	cp -p $< $@

install:
	apt-get install -qqy python-setuptools
	python setup.py install

clean:
	-rm -rf build dist testgrid.egg-info
	-find . -name '*.pyc' -delete

test: NAME :=
test: $(addprefix testgrid/,$(MODULES))
	$(TESTY) -m test.ini $(NAME)

ci:
	git commit -a
	git push
	git push --tags
