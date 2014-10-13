PKGNAME=blivetgui
SPECFILE=blivet-gui.spec
VERSION=$(shell awk '/Version:/ { print $$2 }' $(SPECFILE))
RELEASE=$(shell awk '/Release:/ { print $$2 }' $(SPECFILE) | sed -e 's|%.*$$||g')
RELEASE_TAG=$(PKGNAME)-$(VERSION)-$(RELEASE)
VERSION_TAG=$(PKGNAME)-$(VERSION)

L10N_FILES = po
ZANATA_PULL_ARGS = -B
ZANATA_PUSH_ARGS = -B

all:
	$(MAKE) -C po

po-pull:
	zanata-cli pull $(ZANATA_PULL_ARGS) -s $(L10N_FILES) -t $(L10N_FILES)

potfile:
	$(MAKE) -C po potfile

clean:
	-rm blivetgui/*.pyc blivetgui/*/*.pyc ChangeLog
	$(MAKE) -C po clean
	python setup.py -q clean --all

install:
	python setup.py install --root=$(DESTDIR)
	$(MAKE) -C po install

.PHONY: clean install tag archive local
