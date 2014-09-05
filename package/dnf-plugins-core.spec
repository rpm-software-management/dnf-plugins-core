%global gitrev d8e8044
%global dnf_version 0.5.3

Name:		dnf-plugins-core
Version:	0.1.3
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
BuildRequires:	python-sphinx
BuildRequires:	python2-devel
Requires:	dnf >= %{dnf_version}
Requires:	pykickstart
Requires:	python-requests

%description
Core Plugins for DNF. This package enhance DNF with builddep, copr,
debuginfo-install, download, kickstart, needs-restarting and repoquery
commands. Additionally provides generate_completion_cache, noroot and
protected_packages passive plugins.

%package -n python3-dnf-plugins-core
Summary:	Core Plugins for DNF
Group:		System Environment/Base
BuildRequires:	python3-devel
BuildRequires:	python3-dnf >= %{dnf_version}
BuildRequires:	python3-nose
BuildRequires:	python3-sphinx
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
PYTHONPATH=./plugins /usr/bin/nosetests-2.* -s tests/
PYTHONPATH=./plugins /usr/bin/nosetests-3.* -s tests/

%files -f %{name}.lang
%doc AUTHORS COPYING README.rst
%dir %{_sysconfdir}/dnf/protected.d
%{python_sitelib}/dnf-plugins/*
%{python_sitelib}/dnfpluginscore/
%{_mandir}/man8/dnf.plugin.*

%files -n python3-dnf-plugins-core -f %{name}.lang
%doc AUTHORS COPYING README.rst
%dir %{_sysconfdir}/dnf/protected.d
%{python3_sitelib}/dnf-plugins/*
%{python3_sitelib}/dnfpluginscore/
%{_mandir}/man8/dnf.plugin.*

%changelog

* Thu Sep 4 2014 Jan Silhan <jsilhan@redhat.com> - 0.1.3-1
- repoquery: output times in UTC. (Ales Kozumplik)
- repoquery: missing help messages. (Ales Kozumplik)
- repoquery: add --info. (RhBug:1135984) (Ales Kozumplik)
- add Jan to AUTHORS. (Ales Kozumplik)
- spec: extended package description with plugin names and commands (Related:RhBug:1132335) (Jan Silhan)
- copr: check for 'ok' in 'output' for json data (RhBug:1134378) (Igor Gnatenko)
- README: changed references to new repo location (Jan Silhan)
- transifex update (Jan Silhan)
- copr: convert key to unicode before guessing lenght (Miroslav Suchý)
- Add pnemade to AUTHORS (Ales Kozumplik)
- debuginfo-install: Use logger as module level variable and not instance attribute since dnf-0.6.0 release (RhBug:1130559) (Parag Nemade)
- copr: Use logger as module level variable and not instance attribute since dnf-0.6.0 release (RhBug:1130559) (Parag Nemade)
- copr: implement help command (Igor Gnatenko)
- debuginfo-install: fix indenting (Igor Gnatenko)
- debuginfo-install: use srpm basename for debuginfo (Igor Gnatenko)

* Mon Jul 28 2014 Aleš Kozumplík <ales@redhat.com> - 0.1.2-1
- BashCompletionCache: error strings are unicoded (RhBug:1118809) (Jan Silhan)
- transifex update (Jan Silhan)
- debuginfo-install: remove some pylint warnings (Igor Gnatenko)
- debuginfo-install: fix installing when installed version not found in repos, optimize performance (RhBug: 1108321) (Ig
- fix: copr plugin message for repo without builds (RhBug:1116389) (Adam Samalik)
- logging: remove messages about initialization. (Ales Kozumplik)

* Thu Jul 3 2014 Aleš Kozumplík <ales@redhat.com> - 0.1.1-2
- packaging: add protected_packages.py to the package. (Ales Kozumplik)

* Thu Jul 3 2014 Aleš Kozumplík <ales@redhat.com> - 0.1.1-1
- protected_packages: prevent removal of the running kernel. (RhBug:1049310) (Ales Kozumplik)
- packaging: create and own /etc/dnf/protected.d. (Ales Kozumplik)
- doc: add documentation for protected_packages. (Ales Kozumplik)
- doc: rename: generate-completion-cache -> generate_completion_cache. (Ales Kozumplik)
- add protected_packages (RhBug:1111855) (Ales Kozumplik)
- build: add python-requests to requires (RHBZ: 1104088) (Miroslav Suchý)
- doc: typo: fix double 'plugin' in release notes. (Ales Kozumplik)

* Wed Jun 4 2014 Aleš Kozumplík <ales@redhat.com> - 0.1.0-1
- pylint: fix all pylint builddep problems. (Ales Kozumplik)
- builddep: better error reporting on deps that actually don't exist. (Ales Kozumplik)
- builddep: load available repos. (RhBug:1103906) (Ales Kozumplik)
- tests: stop argparse from printing to stdout when tests run. (Ales Kozumplik)
- packaging: all the manual pages with a glob. (Ales Kozumplik)
- fix: packaging problem with query.py. (Ales Kozumplik)
- doc: add reference documentation for repoquery. (Ales Kozumplik)
- repoquery: support --provides, --requires etc. (Ales Kozumplik)
- repoquery: make the CLI more compatible with Yum's repoquery. (Ales Kozumplik)
- repoquery: some cleanups in the plugin and the tests. (Ales Kozumplik)
- rename: query->repoquery. (RhBug:1045078) (Ales Kozumplik)
- add pylint script for dnf-core-plugins. (Ales Kozumplik)
- tests: repoquery: fix unit tests. (Ales Kozumplik)
- add query tool (Tim Lauridsen)

* Wed May 28 2014 Aleš Kozumplík <ales@redhat.com> - 0.0.8-1
- build: add sphinx to build requires. (Ales Kozumplik)
- doc: packaging: add license block to each .rst. (Ales Kozumplik)
- tests: stray print() in test_download.py. (Ales Kozumplik)
- doc: put each synopsis on new line (Miroslav Suchý)
- doc: cosmetic: project name in the documentation. (Ales Kozumplik)
- doc: cleanups, form, style. (Ales Kozumplik)
- doc: add documentation and man pages (Tim Lauridsen)
- copr: remove repofile if failed to enable repo (Igor Gnatenko)
- copr: honor -y and --assumeno (Miroslav Suchý)
- py3: absolute imports and unicode literals everywhere. (Ales Kozumplik)
- debuginfo-install: doesn't install latest pkgs (RhBug: 1096507) (Igor Gnatenko)
- debuginfo-install: fix description (Igor Gnatenko)
- debuginfo-install: fix logger debug messages (Igor Gnatenko)
- build: install the download plugin (Tim Lauridsen)
- download: update the download plugin with --source, --destdir & --resolve options (Tim Lauridsen)
- Add a special ArgumentParser to parsing plugin cmd arguments and options (Tim Lauridsen)
- tests: add __init__.py to make tests a module and use abs imports (Tim Lauridsen)
- build: simplify plugins/CMakeLists.txt. (Ales Kozumplik)
- dnf.cli.commands.err_mini_usage() changed name. (Ales Kozumplik)
- kickstart: do not include kickstart errors into own messages. (Radek Holy)

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
