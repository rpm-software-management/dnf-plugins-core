PKGNAME = dnf-plugins-core
SUBDIRS = po plugins plugins/dnfplugins
VERSION=$(shell awk '/Version:/ { print $$2 }' package/${PKGNAME}.spec)
TX_PRJ = dnf-plugins-core
TX_RESOURCE = dnf-plugins-core.master

all: subdirs
	
subdirs:
	for d in $(SUBDIRS); do make -C $$d; [ $$? = 0 ] || exit 1 ; done

clean:
	for d in $(SUBDIRS); do make -C $$d clean ; done

install:
	for d in $(SUBDIRS); do make DESTDIR=$(DESTDIR) -C $$d install; [ $$? = 0 ] || exit 1; done

archive:
	@rm -rf ${PKGNAME}-${VERSION}.tar.gz
	@git archive --format=tar --prefix=$(PKGNAME)-$(VERSION)/ HEAD | gzip -9v >${PKGNAME}-$(VERSION).tar.gz
	@cp ${PKGNAME}-$(VERSION).tar.gz $(shell rpm -E '%_sourcedir')
	@rm -rf ${PKGNAME}-${VERSION}.tar.gz
	@echo "The archive is in $(shell rpm -E '%_sourcedir')/${PKGNAME}-$(VERSION).tar.gz"
	
release:
	@git commit -a -m "bumped version to $(VERSION)"
	@git push
	@git tag -f -m "Added ${PKGNAME}-${VERSION} release tag" ${PKGNAME}-${VERSION}
	@git push --tags origin
	
rpms:
	@$(MAKE) archive
	@rpmbuild -ba package/${PKGNAME}.spec
	
transifex-setup:
	tx init
	tx set --auto-remote https://www.transifex.com/projects/p/${TX_PRJ}/
	tx set --auto-local  -r ${TX_RESOURCE} 'po/<lang>.po' --source-lang en --source-file po/${PKGNAME}.pot --execute


transifex-pull:
	tx pull -a -f
	@echo "You can now git commit -a -m 'Transfix pull, *.po update'"

transifex-push:
	make -C po ${PKGNAME}.pot
	tx push -s
	@echo "You can now git commit -a -m 'Transfix push, ${PKGNAME}.pot update'"

FORCE:
	
