%global gitrev 3bb4574
%global dnf_version 0.5.0

Name:		dnf-plugins-core
Version:	0.0.7
Release:	1%{?dist}
Summary:	Core Plugins for DNF
Group:		System Environment/Base
License:	GPLv2+
URL:		https://github.com/akozumpl/dnf-plugins-core

# source archive is created by running package/archive from a git checkout
Source0:	dnf-plugins-core-%{gitrev}.tar.xz

BuildArch:	noarch
BuildRequires:	cmake
BuildRequires:	dnf >= %{dnf_version}
BuildRequires:	gettext
BuildRequires:	pykickstart
BuildRequires:	python-nose
BuildRequires:	python2-devel
Requires:	dnf >= %{dnf_version}
Requires:	pykickstart

%description
Core Plugins for DNF.

%package -n python3-dnf-plugins-core
Summary:	Core Plugins for DNF
Group:		System Environment/Base
BuildRequires:	python3-devel
BuildRequires:	python3-dnf >= %{dnf_version}
BuildRequires:	python3-nose
Requires:	python3-dnf >= %{dnf_version}

%description -n python3-dnf-plugins-core
Core Plugins for DNF, Python 3 version.


%prep
%setup -q -n dnf-plugins-core
rm -rf py3
mkdir ../py3
cp -a . ../py3/
mv ../py3 ./

%build
%cmake .
make %{?_smp_mflags}
make doc-man
pushd py3
%cmake -DPYTHON_DESIRED:str=3 .
make %{?_smp_mflags}
make doc-man
popd

%install
make install DESTDIR=$RPM_BUILD_ROOT
%find_lang %{name}
pushd py3
make install DESTDIR=$RPM_BUILD_ROOT
popd

%check
PYTHONPATH=./plugins nosetests-2.7 -s tests/
PYTHONPATH=./plugins nosetests-3.3 -s tests/

%files -f %{name}.lang
%doc AUTHORS COPYING README.rst
%{python_sitelib}/dnf-plugins/*
%{python_sitelib}/dnfpluginscore/
%{_mandir}/man8/dnf.plugin.*

%files -n python3-dnf-plugins-core -f %{name}.lang
%doc AUTHORS COPYING README.rst
%{python3_sitelib}/dnf-plugins/*
%{python3_sitelib}/dnfpluginscore/
%{_mandir}/man8/dnf.plugin.*

%changelog

* Wed Apr 23 2014 Aleš Kozumplík <ales@redhat.com> - 0.0.7-1
- build: gettext is also needed as a buildreq (Tim Lauridsen)
- copr: use usage & summary class attributes, to work with dnf 0.5.0 use shared lib dnfpluginscore for translation wrapp
- build: add cmake as buildreq (Tim Lauridsen)
- generate-completion-cache: fix shared lib name (Tim Lauridsen)
- make .spec use gitrev in the source file add helper script for building source archive (Tim Lauridsen)
- Added transifex config (Tim Lauridsen)
- tests: use cli logger in kickstart test (Tim Lauridsen)
- Added translation .pot file Added da translation files so we have something to build & install (Tim Lauridsen)
- Added CMake files Added CMake build to .spec & and added translation files handling (Tim Lauridsen)
- make plugins use shared lib added translation wrappers added missing usage & summary PEP8 fixes (Tim Lauridsen)
- added shared dnfpluginscore lib (Tim Lauridsen)
- copr: C:139, 0: Unnecessary parens after 'print' keyword (superfluous-parens) (Miroslav Suchý)
- copr: W: 23, 0: Unused import gettext (unused-import) (Miroslav Suchý)
- copr: C: 33, 0: No space allowed before : (Miroslav Suchý)
- copr: some python3 migration (Miroslav Suchý)
- copr: get rid of dnf i18n imports (Miroslav Suchý)
- remove dnf.yum.i18n imports. (Ales Kozumplik)
- copr: Fix the playground upgrade command. (Tadej Janež)
- copr: implement search function (Igor Gnatenko)
- better format output (Miroslav Suchý)
- implement playground plugin (Miroslav Suchý)
- move removing of repo into method (Miroslav Suchý)
- check root only for actions which really need root (Miroslav Suchý)
- move repo downloading into separate method (Miroslav Suchý)
- define copr url as class attribute (Miroslav Suchý)
- better wording of warning (Miroslav Suchý)
- move question to function argument (Miroslav Suchý)
- move guessing chroot into function (Miroslav Suchý)
- copr: use common lib use Command.usage & summary cleanup imports & PEP8 fixes (Tim Lauridsen)
- builddep: added usage & summary & fix some PEP8 issues (Tim Lauridsen)
- kickstart: use new public Command.usage & Command.summary api (Tim Lauridsen)
- fix resource leak in builddep.py. (Ales Kozumplik)
- refactor: command plugins use demands mechanism. (Ales Kozumplik)
- noroot: move to the new 'demands' mechanism to check the need of root. (Ales Kozumplik)
- tests: fix locale independence. (Radek Holy)
- [copr] correctly specify chroot when it should be guessed (Miroslav Suchý)

* Mon Mar 17 2014 Aleš Kozumplík <ales@redhat.com> - 0.0.6-1
- clenaup: remove commented out code (Miroslav Suchý)
- copr: list: print description (Igor Gnatenko)
- builddep: rpm error messages sink. (Ales Kozumplik)
- builddep: improve error handling on an command argument (RhBug:1074436) (Ales Kozumplik)
- copr: handling case when no argument is passed on cli (Miroslav Suchý)
- copr: delete excess argument (Igor Gnatenko)
- add copr plugin (Miroslav Suchý)
- debuginfo-install: check for root with dnf api (Igor Gnatenko)
- packaging: fix bogus dates. (Ales Kozumplik)

* Wed Feb 26 2014 Aleš Kozumplík <ales@redhat.com> - 0.0.5-2
- packaging: add debuginfo-install.py (Ales Kozumplik)

* Wed Feb 26 2014 Aleš Kozumplík <ales@redhat.com> - 0.0.5-1
- packaging: add builddep.py to the RPM. (Ales Kozumplik)

* Tue Feb 25 2014 Radek Holý <rholy@redhat.com> - 0.0.4-1
- refactor: use Base.install instead of installPkgs in kickstart plugin. (Radek Holy)
- refactor: move kickstart arguments parsing to standalone method. (Radek Holy)
- tests: test effects instead of mock calls. (Radek Holy)
- Add debuginfo-install plugin. (RhBug:1045770) (Igor Gnatenko)
- builddep: needs to be run under root. (RhBug:1065851) (Ales Kozumplik)

* Thu Feb 6 2014 Aleš Kozumplík <ales@redhat.com> - 0.0.3-1
- tests: import mock through support so its simpler for the test cases. (Ales Kozumplik)
- packaging: fix typos in the spec. (Ales Kozumplik)
- [completion_cache] Cache installed packages, update the cache less frequently (Elad Alfassa)
- Add bash completion to dnf (Elad Alfassa)
- packaging: missing buildrequire (Ales Kozumplik)

* Mon Jan 13 2014 Aleš Kozumplík <ales@redhat.com> - 0.0.2-1
- First release.

* Wed Jan 8 2014 Cristian Ciupitu <cristian.ciupitu@yahoo.com> - 0.0.1-4
- Spec updates.

* Tue Jan 7 2014 Aleš Kozumplík <ales@redhat.com> - 0.0.1-3
- Spec updates.

* Mon Jan 6 2014 Aleš Kozumplík <ales@redhat.com> - 0.0.1-2
- Spec updates.

* Fri Dec 20 2013 Aleš Kozumplík <ales@redhat.com> - 0.0.1-1
- The initial package version.
