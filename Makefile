# copyright (c) 2013-2014 smartjog, released under the GPL license.

.PHONY: install update loc

usage::
	@echo "Testgrid build utility."
	@echo
	@echo "Usage:"
	@echo "  make install  install testgrid command-line tool and framework"
	@echo "  make update   update 3rd-party dependencies (reserved)"
	@echo "  make loc      return the number of lines of code"
	@echo

#include template.mk

#
# install for OS/X
#
ifeq ($(shell uname -s), Darwin)
install:
	easy_install pip
	CFLAGS=-Qunused-arguments CPPFLAGS=-Qunused-arguments pip install ansible
	python setup.py install
#
# install for Debian
#
else ifeq ($(shell uname -s), Linux) # FIXME (Debian/Ubuntu only)
install:
	apt-get install -qqy python-setuptools
	apt-get install python-pip
	pip install ansible
	python setup.py install
else
$(error unsupported platform)
endif

update:
	@$(MAKE) -f update.mk

clean::
	-rm -rf build dist testgrid.egg-info
	find . -name '*.pyc' -exec rm \{\} \;
	rm -rf obj

obj:
	mkdir $@

test: 	| obj
#ifeq ($(shell which nosetests),)
	PYTHONPATH=. python test.py
#else
#	nosetests --with-xunit --xunit-file=obj/nosetests.xml test.py

#endif

loc:
	find . \( -name '*.py' -o -name '*.sql' \) -a -not \( -name bottle.py -o -name docopt.py \) | xargs wc -l | sort -n
