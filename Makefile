.PHONY: test

validate:
	python server/model.py
	python validate.py