.PHONY: usage test clean

usage:
	@echo "Reserved:"
	@echo "  make clean  delete bytecode"
	@echo "  make ci     check-in code"
	@echo
	@echo "Changes:"
	git status -s

clean:
	-find . -name '*.pyc' -delete

ci:
	git commit -a
	git push

validate: NAME:=
validate:
	python server/model.py
	python validate.py $(NAME)