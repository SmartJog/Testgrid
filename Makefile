# copyright (c) 2013-2014 smartjog, released under the GPL license.

.PHONY: usage test clean

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

clean:
	-find . -name '*.pyc' -delete

ci:
	git commit -a
	git push

test: NAME:=
test:
	python testgrid/server/model.py
	python testgrid/server/parser.py
	#python testgrid/client/model.py
	#python test.py $(NAME)

install:
	sudo apt-get install -qqy python-setuptools
	sudo python setup.py install

deepclean: clean
	-rm -rf build dist testgrid.egg-info

server:
	python -m testgrid.server.rest
