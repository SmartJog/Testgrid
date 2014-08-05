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

obj/tgc: 	obj
			cp cli/controller_main.py obj/tgc
			cp cli/main.py obj/tg

test: 	| obj
ifeq ($(shell which nosetests),)
	python -m unittest -v testgrid.model testgrid.controller testgrid.database testgrid.persistent testgrid.client testgrid.isadapter testgrid.rest
else
	nosetests --with-xunit --xunit-file=obj/nosetests.xml -v testgrid.model testgrid.controller testgrid.database testgrid.persistent testgrid.client testgrid.isadapter testgrid.rest

endif

loc:
	find . \( -name '*.py' -o -name '*.sql' \) -a -not \( -name bottle.py -o -name docopt.py \) | xargs wc -l | sort -n


deb: VERSION:=1.0
deb: clean obj/tgc
	cp -r deb obj/tgc_$(VERSION)
	sed -e 's/__VERSION__/$(VERSION)/g' -i obj/tgc_$(VERSION)/DEBIAN/control
	mkdir -p obj/tgc_$(VERSION)/usr/local/sbin
	cp obj/tgc obj/tgc_$(VERSION)/usr/local/sbin
	cp obj/tg obj/tgc_$(VERSION)/usr/local/sbin
	chmod +x obj/tgc_$(VERSION)/usr/local/sbin/tg
	chmod +x obj/tgc_$(VERSION)/usr/local/sbin/tgc
#	chmod 755 obj/tgc_$(VERSION)/etc/init.d/tgc
	mkdir -p obj/tgc_$(VERSION)/usr/lib/python2.7
	cp -r testgrid/ obj/tgc_$(VERSION)/usr/lib/python2.7
	fakeroot dpkg-deb --build obj/tgc_$(VERSION)

deb-rest: VERSION:=1.0
deb-rest: clean obj/tgc
	cp -r deb-rest obj/tg_$(VERSION)
	sed -e 's/__VERSION__/$(VERSION)/g' -i obj/tg_$(VERSION)/DEBIAN/control
	mkdir -p obj/tg_$(VERSION)/usr/local/sbin
	cp obj/tg obj/tg_$(VERSION)/usr/local/sbin
	chmod +x obj/tg obj/tgc_$(VERSION)/usr/local/sbin/tg
	mkdir -p obj/tg_$(VERSION)/usr/lib/python2.7
	cp -r testgrid/ obj/tg_$(VERSION)/usr/lib/python2.7
	fakeroot dpkg-deb --build obj/tg_$(VERSION)