#
# Makefile for the PO files (translation) catalog
#
# $Id$

TOP	 = ..

# What is this package?
NLSPACKAGE	= blivet-gui
POTFILE		= $(NLSPACKAGE).pot
INSTALL		= /usr/bin/install -c
INSTALL_DATA	= $(INSTALL) -m 644
INSTALL_DIR	= /usr/bin/install -d

# destination directory
INSTALL_NLS_DIR = $(RPM_BUILD_ROOT)/usr/share/locale

# PO catalog handling
MSGMERGE	= msgmerge -v
XGETTEXT	= $(TOP)/translation-canary/xgettext_werror.sh --default-domain=$(NLSPACKAGE) \
		  --add-comments
MSGFMT		= msgfmt --statistics --verbose

# What do we need to do
POFILES		= $(wildcard *.po)
MOFILES		= $(patsubst %.po,%.mo,$(POFILES))
PYSRC		= $(wildcard ../blivetgui/*.py ../blivetgui/*/*.py)
GLADEFILES 	= $(wildcard ../data/ui/*.ui)

all::update-po $(MOFILES)
	@rm -rf tmp

potfile: $(PYSRC) $(GLADEFILES)
	$(XGETTEXT) --keyword=_ --keyword=N_ --keyword=P_:1,2 $(PYSRC) $(GLADEFILES) --from-code utf-8
	@if cmp -s $(NLSPACKAGE).po $(POTFILE); then \
	    rm -f $(NLSPACKAGE).po; \
	else \
	    mv -f $(NLSPACKAGE).po $(POTFILE); \
	fi; \

update-po: Makefile potfile refresh-po

refresh-po: Makefile
	for cat in $(POFILES); do \
		lang=`basename $$cat .po`; \
		if $(MSGMERGE) $$lang.po $(POTFILE) > $$lang.pot ; then \
			mv -f $$lang.pot $$lang.po ; \
			echo "$(MSGMERGE) of $$lang succeeded" ; \
		else \
			echo "$(MSGMERGE) of $$lang failed" ; \
			rm -f $$lang.pot ; \
		fi \
	done

clean:
	@rm -fv *mo *~ .depend
	@rm -rf tmp

install: $(MOFILES)
	@for n in $(MOFILES); do \
	    l=`basename $$n .mo`; \
	    $(INSTALL_DIR) $(INSTALL_NLS_DIR)/$$l/LC_MESSAGES; \
	    $(INSTALL_DATA) --verbose $$n $(INSTALL_NLS_DIR)/$$l/LC_MESSAGES/$(NLSPACKAGE).mo; \
	done

%.mo: %.po
	$(MSGFMT) -o $@ $<

.PHONY: missing depend

