# copyright (c) 2013-2014 smartjog, released under the GPL license.

.PHONY: install loc

usage::
	@echo "Testgrid build utility."
	@echo
	@echo "Usage:"
	@echo "  make install  install testgrid command-line tool and framework"
	@echo "  make loc      return the number of lines of code"
	@echo

include template.mk

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

clean::
	-rm -rf build dist testgrid.egg-info

loc:
	find . \( -name '*.py' -o -name '*.sql' \) -a -not \( -name bottle.py -o -name docopt.py \) | xargs wc -l | sort -n
	