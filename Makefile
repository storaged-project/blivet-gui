PKGNAME=blivetgui
APPNAME=blivet-gui
SPECFILE=blivet-gui.spec
VERSION=$(shell awk '/Version:/ { print $$2 }' $(SPECFILE))
RELEASE=$(shell awk '/Release:/ { print $$2 }' $(SPECFILE))
RELEASE_TAG=$(APPNAME)-$(VERSION)-$(RELEASE)
VERSION_TAG=$(APPNAME)-$(VERSION)

L10N_FILES = po
ZANATA_PULL_ARGS = -B
ZANATA_PUSH_ARGS = -B

all:
	$(MAKE) -C po

po-pull:
	zanata-cli pull $(ZANATA_PULL_ARGS) -s $(L10N_FILES) -t $(L10N_FILES)

po-push: potfile
	zanata-cli push $(ZANATA_PUSH_ARGS) -s $(L10N_FILES) -t $(L10N_FILES)

potfile:
	$(MAKE) -C po potfile

clean:
	-rm blivetgui/*.pyc blivetgui/*/*.pyc ChangeLog
	$(MAKE) -C po clean
	python setup.py -q clean --all

install:
	python setup.py install --root=$(DESTDIR)
	$(MAKE) -C po install

ChangeLog:
	(GIT_DIR=.git git log > .changelog.tmp && mv .changelog.tmp ChangeLog; rm -f .changelog.tmp) || (touch ChangeLog; echo 'git directory not found: installing possibly empty changelog.' >&2)

tag:
	@if test $(RELEASE) = "1" ; then \
	  tags='$(VERSION_TAG) $(RELEASE_TAG)' ; \
	else \
	  tags='$(RELEASE_TAG)' ; \
	fi ; \
	for tag in $$tags ; do \
	  git tag -a -m "Tag as $$tag" -f $$tag ; \
	  echo "Tagged as $$tag" ; \
	done

release: check tag archive

archive: po-pull
	@rm -f ChangeLog
	@make ChangeLog
	git archive --format=tar --prefix=$(APPNAME)-$(VERSION)/ $(VERSION_TAG) > $(APPNAME)-$(VERSION).tar
	mkdir $(APPNAME)-$(VERSION)
	cp -r po $(APPNAME)-$(VERSION)
	cp ChangeLog $(APPNAME)-$(VERSION)/
	tar -rf $(APPNAME)-$(VERSION).tar $(APPNAME)-$(VERSION)
	gzip -9 $(APPNAME)-$(VERSION).tar
	rm -rf $(APPNAME)-$(VERSION)
	git checkout -- po/$(APPNAME).pot
	@echo "The archive is in $(APPNAME)-$(VERSION).tar.gz"

rpmlog:
	@git log --pretty="format:- %s (%ae)" $(RELEASE_TAG).. |sed -e 's/@.*)/)/'
	@echo

.PHONY: check clean install tag archive local
