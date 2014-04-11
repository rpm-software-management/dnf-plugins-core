INSTALL= /usr/bin/install -c
INSTALL_PROGRAM= ${INSTALL}
INSTALL_DATA= ${INSTALL} -m 644
INSTALLNLSDIR=$(DESTDIR)/usr/share/locale
top_srcdir = "."


MSGMERGE = intltool-update -x --gettext-package=$(NLSPACKAGE) --dist

NLSPACKAGE = dnf-plugins-core

CATALOGS = $(shell ls *.po)
FMTCATALOGS = $(patsubst %.po,%.mo,$(CATALOGS))

PYFILES  = $(wildcard ../plugins/*.py)
POTFILES  = $(PYFILES) 

all: $(NLSPACKAGE).pot $(FMTCATALOGS)

POTFILES.in:
	for file in $(POTFILES); do \
		echo "$${file#../}" ; \
	done > $@


$(NLSPACKAGE).pot: $(POTFILES) POTFILES.in
	intltool-update --gettext-package=$(NLSPACKAGE) --pot

clean:
	@rm -fv *mo *~ .depend *.autosave
   
distclean: clean
	rm -f *mo .depend $(NLSPACKAGE).pot POTFILES.in

depend:

install:	all
	mkdir -p $(PREFIX)/$(INSTALLNLSDIR)
	for n in $(CATALOGS); do \
	    l=`basename $$n .po`; \
	    mo=$$l.mo; \
	    if [ ! -f $$mo ]; then continue; fi; \
	    $(INSTALL) -m 755 -d $(PREFIX)/$(INSTALLNLSDIR)/$$l; \
	    $(INSTALL) -m 755 -d $(PREFIX)/$(INSTALLNLSDIR)/$$l/LC_MESSAGES; \
	    $(INSTALL) -m 644 $$mo \
		$(PREFIX)/$(INSTALLNLSDIR)/$$l/LC_MESSAGES/$(NLSPACKAGE).mo; \
	done

%.mo: %.po
	msgfmt -o $@ $<
