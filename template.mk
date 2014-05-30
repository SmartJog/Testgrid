# copyright (c) 2014 fclaerhout.fr, released under the MIT license.

# Generic makefile with generic rules.
#
# Usage:
#   * copy this file into your project directory
#   * create a Makefile, add "include template.mk"
#   * you'll need testy to run tests.

VERSION := "1.2"

.PHONY: usage version clean test log ci

#########
# usage #
#########

usage::
	@echo "Development:"
	@echo "  make version  show compiler and interpreter versions"
	@echo "  make clean    remove generated objects"
	@echo "  make test     run tests"
	@echo "  make log      show ci history"
	@echo "  make ci       check-in: commit and push"
ifeq ($(shell test -d .git && echo ok || echo ko),ok)
	@echo
	@echo "Changes:"
	@git status -s
endif

############
# versions #
############

version:
	@bash --version
	@javac -version
	@node --version
	@go version
	@cc --version

#########
# clean #
#########

clean::
	-find . \( -name '*.pyc' -or -name '*.o' \) -delete

########
# test #
########

ifeq ($(shell which testy),)
test: $(addprefix testgrid/,$(MODULES))
	@echo please install http://fclaerhout.fr/testy
else
test: NAME :=
test: test.ini
	@testy -m test.ini $(NAME)
endif

#######
# log #
#######

log:
	@git log --graph --pretty=format:'%Cred%h%Creset:%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit --

############
# check-in #
############

ci:: TAG :=
ci:: clean
	-git commit -a
	git push
ifeq ($(TAG),)
	$(info commit untagged)
else
	$(info commit tagged as $(TAG))
	git tag $(TAG)
	git push --tags
endif
