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

TEST_DEPENDENCIES += python3-mock
TEST_DEPENDENCIES += python3-coverage
TEST_DEPENDENCIES += python3-pocketlint python3-bugzilla
TEST_DEPENDENCIES += python3-pep8
TEST_DEPENDENCIES += xorg-x11-server-Xvfb
TEST_DEPENDENCIES := $(shell echo $(sort $(TEST_DEPENDENCIES)) | uniq)

all:
	$(MAKE) -C po

po-pull:
	rpm -q zanata-python-client &>/dev/null || ( echo "need to run: yum install zanata-python-client"; exit 1 )
	zanata pull $(ZANATA_PULL_ARGS)

po-push: potfile
	zanata push

potfile:
	$(MAKE) -C po potfile

check-requires:
	@echo "*** Checking if the dependencies required for testing and analysis are available ***"
	@status=0 ; \
	for pkg in $(TEST_DEPENDENCIES) ; do \
		test_output="$$(rpm -q --whatprovides "$$pkg")" ; \
		if [ $$? != 0 ]; then \
			echo "$$test_output" ; \
			status=1 ; \
		fi ; \
	done ; \
	exit $$status

install-requires:
	@echo "*** Installing the dependencies required for testing and analysis ***"
	dnf install -y $(TEST_DEPENDENCIES)

test: check-requires
	@echo "*** Running unittests ***"
	PYTHONPATH=.:tests/ xvfb-run python3 -m unittest discover -v -s tests/ -p '*_test.py'

coverage: check-requires
	@echo "*** Running unittests with $(COVERAGE) for $(PYTHON) ***"
	PYTHONPATH=.:tests/ $(COVERAGE) run --branch -m unittest discover -v -s tests/ -p '*_test.py'
	$(COVERAGE) report --include="blivetgui/*" --show-missing

pylint: check-requires
	@echo "*** Running pylint ***"
	PYTHONPATH=. tests/pylint/runpylint.py

pep8: check-requires
	@echo "*** Running pep8 compliance check ***"
	python3-pep8 --ignore=E501,E402,E731 blivetgui/ tests/ blivet-gui blivet-gui-daemon

canary: check-requires
	$(MAKE) -C po potfile
	PYTHONPATH=translation-canary:$(PYTHONPATH) python3 -m translation_canary.translatable po/blivet-gui.pot

check:
	@status=0; \
	$(MAKE) pylint || status=1; \
	$(MAKE) pep8 || status=1; \
	$(MAKE) canary || status=1; \
	exit $$status

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
	$(MAKE) -B ChangeLog
	git archive --format=tar --prefix=$(APPNAME)-$(VERSION)/ $(VERSION_TAG) | tar -xf -
	cp -r po $(APPNAME)-$(VERSION)
	cp ChangeLog $(APPNAME)-$(VERSION)/
	( cd $(APPNAME)-$(VERSION) && python3 setup.py -q sdist --dist-dir .. )
	rm -rf $(APPNAME)-$(VERSION)
	git checkout -- po/$(APPNAME).pot
	@echo "The archive is in $(APPNAME)-$(VERSION).tar.gz"

local: po-pull
	@make -B ChangeLog
	@python3 setup.py -q sdist --dist-dir .
	@echo "The archive is in $(APPNAME)-$(VERSION).tar.gz"

bumpver:
	@NEWSUBVER=$$((`echo $(VERSION) |cut -d . -f 3` + 1)) ; \
	NEWVERSION=`echo $(VERSION).$$NEWSUBVER |cut -d . -f 1,2,4` ; \
	DATELINE="* `LANG="en_US" date "+%a %b %d %Y"` `git config user.name` <`git config user.email`> - $$NEWVERSION-1"  ; \
	cl=`grep -n %changelog blivet-gui.spec |cut -d : -f 1` ; \
	tail --lines=+$$(($$cl + 1)) blivet-gui.spec > speclog ; \
	(head -n $$cl blivet-gui.spec ; echo "$$DATELINE" ; make --quiet rpmlog 2>/dev/null ; echo ""; cat speclog) > blivet-gui.spec.new ; \
	mv blivet-gui.spec.new blivet-gui.spec ; rm -f speclog ; \
	sed -i "s/Version: $(VERSION)/Version: $$NEWVERSION/" blivet-gui.spec ; \
	sed -i "s/version='$(VERSION)'/version='$$NEWVERSION'/" setup.py ; \
	sed -i "s/APP_VERSION\ =\ '$(VERSION)'/APP_VERSION\ =\ '$$NEWVERSION'/" blivet-gui ; \
	sed -i "s/APP_VERSION\ =\ '$(VERSION)'/APP_VERSION\ =\ '$$NEWVERSION'/" blivetgui/logs.py ; \

rpmlog:
	@git log --pretty="format:- %s (%ae)" $(RELEASE_TAG).. |sed -e 's/@.*)/)/'
	@echo

ci: check test

.PHONY: check pep8 pylint clean install tag archive local
