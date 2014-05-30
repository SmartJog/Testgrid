REP1 := ~/Documents/work/0kit
REP2 := ~/Documents/work/qap
DEPS :=\
	$(addprefix testgrid/, strfmt.py docopt.py vagrant.py bottle.py installsystems.py)\
	template.mk

.PHONY: all lock

all: $(DEPS) lock

%: $(REP1)/%
	cp -f $< $@

testgrid/%: $(REP1)/%
	cp -f $< $@

testgrid/%: $(REP2)/%
	cp -f $< $@

lock:
	chmod a-w $(DEPS)
