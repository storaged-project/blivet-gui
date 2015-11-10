PKGNAME=blivetgui
APPNAME=blivet-gui
SPECFILE=blivet-gui.spec
VERSION=$(shell awk '/Version:/ { print $$2 }' $(SPECFILE))
RELEASE=$(shell awk '/Release:/ { print $$2 }' $(SPECFILE) | sed -e 's|%.*$$||g')
RELEASE_TAG=$(VERSION)-$(RELEASE)
VERSION_TAG=$(VERSION)

ZANATA_PULL_ARGS = --transdir ./
ZANATA_PUSH_ARGS = --srcdir ./ --push-type source --force
PYTHON=python3
COVERAGE=coverage3

all:
	$(MAKE) -C po

po-pull:
	rpm -q zanata-python-client &>/dev/null || ( echo "need to run: yum install zanata-python-client"; exit 1 )
	zanata pull $(ZANATA_PULL_ARGS)

po-push: potfile
	zanata push

potfile:
	$(MAKE) -C po potfile

test:
	@echo "*** Running unittests ***"
	PYTHONPATH=.:tests/ python3 -m unittest discover -v -s tests/ -p '*_test.py'

coverage:
	@echo "*** Running unittests with $(COVERAGE) for $(PYTHON) ***"
	PYTHONPATH=.:tests/ $(COVERAGE) run --branch -m unittest discover -v -s tests/ -p '*_test.py'
	$(COVERAGE) report --include="blivetgui/*" --show-missing

check:
	PYTHONPATH=. tests/pylint/runpylint.py

clean:
	-rm blivetgui/*.pyc blivetgui/*/*.pyc ChangeLog
	$(MAKE) -C po clean
	$(PYTHON) setup.py -q clean --all

install:
	$(PYTHON) setup.py install --root=$(DESTDIR)
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

release: tag archive

archive: po-pull
	@rm -f ChangeLog
	$(MAKE) ChangeLog
	git archive --format=tar --prefix=$(APPNAME)-$(VERSION)/ $(RELEASE_TAG) > $(APPNAME)-$(VERSION).tar
	mkdir $(APPNAME)-$(VERSION)
	cp -r po $(APPNAME)-$(VERSION)
	cp ChangeLog $(APPNAME)-$(VERSION)/
	tar -rf $(APPNAME)-$(VERSION).tar $(APPNAME)-$(VERSION)
	gzip -9 $(APPNAME)-$(VERSION).tar
	rm -rf $(APPNAME)-$(VERSION)
	git checkout -- po/$(APPNAME).pot
	@echo "The archive is in $(APPNAME)-$(VERSION).tar.gz"

local: po-pull
	@rm -f ChangeLog
	@make ChangeLog
	@rm -rf $(APPNAME)-$(VERSION).tar.gz
	@rm -rf /tmp/$(APPNAME)-$(VERSION) /tmp/$(APPNAME)
	@dir=$$PWD; cp -a $$dir /tmp/$(APPNAME)-$(VERSION)
	@cd /tmp/$(APPNAME)-$(VERSION) ; $(PYTHON) setup.py -q sdist
	@cp /tmp/$(APPNAME)-$(VERSION)/dist/$(APPNAME)-$(VERSION).tar.gz .
	@rm -rf /tmp/$(APPNAME)-$(VERSION)
	@echo "The archive is in $(APPNAME)-$(VERSION).tar.gz"

bumpver:
	@NEWSUBVER=$$((`echo $(VERSION) |cut -d . -f 2` + 1)) ; \
	NEWVERSION=`echo $(VERSION).$$NEWSUBVER |cut -d . -f 1,3` ; \
	DATELINE="* `LANG="en_US" date "+%a %b %d %Y"` `git config user.name` <`git config user.email`> - $$NEWVERSION-1"  ; \
	cl=`grep -n %changelog blivet-gui.spec |cut -d : -f 1` ; \
	tail --lines=+$$(($$cl + 1)) blivet-gui.spec > speclog ; \
	(head -n $$cl blivet-gui.spec ; echo "$$DATELINE" ; make --quiet rpmlog 2>/dev/null ; echo ""; cat speclog) > blivet-gui.spec.new ; \
	mv blivet-gui.spec.new blivet-gui.spec ; rm -f speclog ; \
	sed -i "s/Version: $(VERSION)/Version: $$NEWVERSION/" blivet-gui.spec ; \
	sed -i "s/version='$(VERSION)'/version='$$NEWVERSION'/" setup.py ; \
	sed -i "s/APP_VERSION\ =\ '$(VERSION)'/APP_VERSION\ =\ '$$NEWVERSION'/" blivet-gui ; \
	sed -i "s/APP_VERSION\ =\ '$(VERSION)'/APP_VERSION\ =\ '$$NEWVERSION'/" blivetgui/logs.py ; \
	$(MAKE) po-push
	$(MAKE) -C po clean

rpmlog:
	@git log --pretty="format:- %s (%ae)" $(RELEASE_TAG).. |sed -e 's/@.*)/)/'
	@echo

.PHONY: check clean install tag archive local
