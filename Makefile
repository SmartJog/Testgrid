.PHONY: usage test clean

usage:
	@echo "Usage:"
	@echo "  ...to be completed later..."
	@echo
	@echo "Reserved:"
	@echo "  make validate  run test cases validating the implementation"
	@echo "  make clean     delete bytecode"
	@echo "  make ci        check-in code"
	@echo
	@echo "Changes:"
	@git status -s

clean:
	-find . -name '*.pyc' -delete

ci:
	git commit -a
	git push

validate: NAME:=
validate:
	python testgrid/server/model.py
	python validate.py $(NAME)

install:
	sudo apt-get install -qqy python-setuptools
	sudo python setup.py install

deepclean: clean
	-rm -rf build dist testgrid.egg-info
