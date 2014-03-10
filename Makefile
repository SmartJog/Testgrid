.PHONY: test

validate: NAME:=
validate:
	python server/model.py
	python validate.py $(NAME)