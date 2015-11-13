%{?!dnf_lowest_compatible: %global dnf_lowest_compatible 1.1.4}
%{?!dnf_not_compatible: %global dnf_not_compatible 2.0}
%global hawkey_version 0.6.1

Name:       dnf-plugins-core
Version:    0.1.13
Release:    1%{?snapshot}%{?dist}
Summary:    Core Plugins for DNF
Group:      System Environment/Base
License:    GPLv2+
URL:        https://github.com/rpm-software-management/dnf-plugins-core
# source archive is created by running package/archive from a git checkout
Source0:    dnf-plugins-core-%{version}.tar.gz
BuildArch:  noarch
BuildRequires:  cmake
BuildRequires:  gettext
%if 0%{?fedora} >= 23
Requires:   python3-dnf-plugins-core = %{version}-%{release}
Conflicts:  python-dnf-plugins-core <= 0.1.6-2
%else
Requires:   python-dnf-plugins-core = %{version}-%{release}
Conflicts:  python3-dnf-plugins-core <= 0.1.6-2
%endif
Provides:   dnf-command(builddep)
Provides:   dnf-command(config-manager)
Provides:   dnf-command(copr)
Provides:   dnf-command(debuginfo-install)
Provides:   dnf-command(download)
Provides:   dnf-command(repoquery)
Provides:   dnf-command(reposync)
%description
Core Plugins for DNF. This package enhance DNF with builddep, config-manager,
copr, debuginfo-install, download, needs-restarting, repoquery and
reposync commands. Additionally provides generate_completion_cache, noroot and
protected_packages passive plugins.

%package -n python-dnf-plugins-core
Summary:    Core Plugins for DNF
Group:      System Environment/Base
BuildRequires:  python2-dnf >= %{dnf_lowest_compatible}
BuildRequires:  python2-dnf < %{dnf_not_compatible}
BuildRequires:  python-nose
BuildRequires:  python-sphinx
BuildRequires:  python2-devel
Requires:   python2-dnf >= %{dnf_lowest_compatible}
Requires:   python2-dnf < %{dnf_not_compatible}
Requires:   python-hawkey >= %{hawkey_version}
Conflicts:  dnf-plugins-core <= 0.1.5
%description -n python-dnf-plugins-core
Core Plugins for DNF, Python 2 interface. This package enhance DNF with builddep, copr,
config-manager, debuginfo-install, download, needs-restarting, repoquery and
reposync commands. Additionally provides generate_completion_cache, noroot and
protected_packages passive plugins.

%package -n python3-dnf-plugins-core
Summary:    Core Plugins for DNF
Group:      System Environment/Base
BuildRequires:  python3-devel
BuildRequires:  python3-dnf >= %{dnf_lowest_compatible}
BuildRequires:  python3-dnf < %{dnf_not_compatible}
BuildRequires:  python3-nose
BuildRequires:  python3-sphinx
Requires:   python3-dnf >= %{dnf_lowest_compatible}
Requires:   python3-dnf < %{dnf_not_compatible}
Requires:   python3-hawkey >= %{hawkey_version}
Conflicts:  dnf-plugins-core <= 0.1.5
%description -n python3-dnf-plugins-core
Core Plugins for DNF, Python 3 interface. This package enhance DNF with builddep, copr,
config-manager, debuginfo-install, download, needs-restarting, repoquery and
reposync commands. Additionally provides generate_completion_cache, noroot and
protected_packages passive plugins.

%prep
%setup -q -n dnf-plugins-core-%{version}
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
%find_lang dnf-plugins-core
pushd py3
make install DESTDIR=$RPM_BUILD_ROOT
popd

%check
PYTHONPATH=./plugins /usr/bin/nosetests-2.* -s tests/
PYTHONPATH=./plugins /usr/bin/nosetests-3.* -s tests/

%files
%{_mandir}/man8/dnf.plugin.*

%files -n python-dnf-plugins-core -f %{name}.lang
%doc AUTHORS COPYING README.rst
%dir %{_sysconfdir}/dnf/protected.d
%ghost %{_var}/cache/dnf/packages.db
%{python_sitelib}/dnf-plugins/*
%{python_sitelib}/dnfpluginscore/

%files -n python3-dnf-plugins-core -f %{name}.lang
%doc AUTHORS COPYING README.rst
%dir %{_sysconfdir}/dnf/protected.d
%ghost %{_var}/cache/dnf/packages.db
%exclude %{python3_sitelib}/dnf-plugins/__pycache__/
%exclude %{python3_sitelib}/dnf-plugins/kickstart.py
%{python3_sitelib}/dnf-plugins/*
%{python3_sitelib}/dnf-plugins/__pycache__/*
%{python3_sitelib}/dnfpluginscore/

%changelog
* Wed Oct 14 2015 Jan Silhan <jsilhan@redhat.com> 0.1.13-1
- updated: release notes for 0.1.13 (Jan Silhan)
- Remove kickstart plugin from core plugins (Neal Gompa
  (ニール・ゴンパ))
- read file as utf-8 in Py3 (RhBug:1267808) (Miroslav Suchý)
- playground: check if repo actually exists for our version of OS (Miroslav
  Suchý)
- add Catalan (Robert Antoni Buj Gelonch)
- repoquery: Fix UnicodeEncodeError with --info (RhBug:1264125) (Jaroslav
  Mracek)
- lookup builddeps in source package for given package name (RhBug:1265622)
  (Michael Mraka)
- functions moved to library (Michael Mraka)
- functions to return name of source and debuginfo package (Michael Mraka)
- try <name>-debuginfo first then <srcname>-debuginfo (RhBug:1159614) (Michael
  Mraka)
- Automatic commit of package [dnf-plugins-core] release [0.1.12-2]. (Michal
  Luscon)
- doc: release notes 0.1.12 (Michal Luscon)

* Tue Sep 22 2015 Michal Luscon <mluscon@redhat.com> 0.1.12-2
- add python2-dnf requirements

* Tue Sep 22 2015 Michal Luscon <mluscon@redhat.com> 0.1.12-1
- repoquery: add globbing support to whatrequires/whatprovides.
  (RhBug:1249073) (Valentina Mukhamedzhanova)
- needs_restarting: Rewrite a warning message (Wieland Hoffmann)
- Remove extra quotation mark in comment (Alexander Todorov)

* Tue Sep 01 2015 Michal Luscon <mluscon@redhat.com> 0.1.11-1
- dnf donwload checks for duplicate packages (rhBug:1250114) (Adam Salih)
- Extend repoquery --arch option. You can now pass multiple archs separated by
  commas (RhBug:1186381) (Adam Salih)
- download plugin now prints not valid packages (RhBug:1225784) (Adam Salih)
- correct typo (Adam Salih)
- dnf now accepts more than one key (RhBug:1233728) (Adam Salih)
- description should be print unwrapped (Adam Salih)
- alternative to pkgnarrow (RhBug:1199601) (Adam Salih)
- sort output alphabetically, tree accepts switches --enhances --suggests
  --provides --suplements --recommends (RhBug:1156778) (Adam Salih)

* Mon Aug 10 2015 Jan Silhan <jsilhan@redhat.com> 0.1.10-1
- generate_completion_cache: use list for each insert (fixes regression
  introduced in e020c96) (Igor Gnatenko)
- generate_completion_cache: store NEVRA insted of NA (RhBug:1226663) (Igor
  Gnatenko)
- repoquery: weak deps queries (RhBug:1184930) (Michal Luscon)
- builddep requires an argument (Michael Mraka)
- disable c++ checks in rpmbuild (Michael Mraka)
- path may contain unicode (RhBug:1234099) (Michael Mraka)
- fail if no package match (RhBug:1241126) (Michael Mraka)
- make --spec and --srpm mutually exclusive (Michael Mraka)
- handle error message in python3 (RhBug:1218299) (Michael Mraka)
- options to recognize spec/srpm files (RhBug:1241135) (Michael Mraka)
- copr: set chmod to rw-r--r-- on repo files (Miroslav Suchý)
- [copr] refactor duplicated lines (Jakub Kadlčík)
- [copr] allow utf-8 user input (RhBug:1244125) (Jakub Kadlčík)
- [copr] fix regression with handling `search` and `list` subcommands (Valentin
  Gologuzov)
- [copr] terminate execution when failed to parse project name (Valentin
  Gologuzov)
- [copr] unused import (Valentin Gologuzov)
- [copr] subcommand `disable` now only set `enabled=0`, repo file could be
  deleted by new subcommand `remove` (Valentin Gologuzov)

* Wed Jun 24 2015 Michal Luscon <mluscon@redhat.com> 0.1.9-1
- repoquery: add srpm option (RhBug:1186382) (Vladan Kudlac)
- create repo files readable by users (RhBug:1228693) (Michael Mraka)
- copr: use librepo instead of python-request (Miroslav Suchý)
- --tree now works with --conflicts --obsoletes --requires and --whatrequires
  (RhBug:1128424) (RhBug:1186689) (Adam Salih)
- url for copr repos changed (RhBug:1227190) (Miroslav Suchý)
- repoquery: fixed conflicts package format (Adam Salih)
- document that globs can be used in dnf config-manager (Michael Mraka)


* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.1.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed May 06 2015 Michal Luscon <mluscon@redhat.com> 0.1.8-1
- spec: fix an upgrade path from dnf-plugins-core <= 0.1.5 (Radek Holy)

* Thu Apr 30 2015 Michal Luscon <mluscon@redhat.com> 0.1.7-1
- doc: release notes dnf-plugins-core-0.1.7 (Michal Luscon)
- spec: fix Conflicts of the new plugins (Radek Holy)
- spec: allow DNF 1.x.x (Radek Holy)
- AUTHORS: filled in missing email address (Jan Silhan)
- download: enabling source repos when desired only (Jan Silhan)
- download: using enable_source_repos from lib (Jan Silhan)
- lib: inform user when enabling disabled repo (Jan Silhan)
- AUTHORS: made 2 categories (Jan Silhan)
- fixed typos and missing demand (Michael Mraka)
- changed warning paragraph (Michael Mraka)
- AUTHORS: updated (Jan Silhan)
- debuginfo-install: don't consider src packages as candidates for installation
  (RhBug:1215154) (Lubomir Rintel)
- documentation warning about build deps in srpm (Michael Mraka)
- fixed builddep tests (Michael Mraka)
- builddep: enable source repos only when needed (Michael Mraka)
- fixed builldep documentation (Michael Mraka)
- mark appropriate dnfpluginscore.lib as API (Michael Mraka)
- fixed builddep configure test (Michael Mraka)
- moved enable_{source|debug}_repos() to dnfpluginscore.lib (Michael Mraka)
- builddep: add feature to get builddeps from remote packages (RhBug:1074585)
  (Igor Gnatenko)
- doc: repoquery: doesn't print 'No match for argument:...' garbage (Jan
  Silhan)
- updated repoquery documentation (Michael Mraka)
- implemented repoquery --latest-limit (Michael Mraka)
- implemented repoquery --unsatisfied (Michael Mraka)
- builddep: Support defining macros for parsing spec files (David Michael)
- removed redundant argument (Michael Mraka)
- doc: update repoquery docs with --resolve (Tim Lauridsen)
- repoquery: add --resolve option (RhBug:1156487) (Tim Lauridsen)
- spec: dnf version upper boundaries (Jan Silhan)
- spec: added plugin command provides (Related:RhBug:1208773) (Jan Silhan)
- make --repo cumulative (Michael Mraka)
- rename --repoid to --repo (Michael Mraka)
- don't delete local repo packages after download (RhBug:1186948) (Michael
  Mraka)
- doc: replaced last references pointing to akozumpl (Jan Silhan)

* Wed Apr 08 2015 Michal Luscon <mluscon@redhat.com> 0.1.6-3
- doc: release notes 0.1.6 (Michal Luscon)
- initialize to use tito (Michal Luscon)
- prepare repo for tito build system (Michal Luscon)
- migrate raw_input() to Python3 (RhBug:1208399) (Miroslav Suchý)
- require dnf 0.6.5+ which contains duplicated/installonly queries (Michael Mraka)
- implemented --duplicated and --installonly (Michael Mraka)
- create --destdir if not exist (Michael Mraka)
- repoquery: Added -s/--source switch, test case and documentation for querying source rpm name (Parag Nemade)
- repoquery: Added documentation and test case for file switch (Parag Nemade)
- spec: ship man pages in dnf-plugins-core metapackage (Jan Silhan)
- debuginfo-install: support cases where src.rpm name != binary package name (Petr Spacek)
- spec: added empty %files directive to generate rpm (Jan Silhan)
- spec: adapt to pykickstart f23 package split (Jan Silhan)
- spec: requires >= dnf version not = (Jan Silhan)
- spec: python3 source code by default in f23+ (RhBug:1194725,1198442) (Jan Silhan)
- use dnfpluginscore.lib.urlopen() (RhBug:1193047) (Miroslav Suchý)
- implemented functionality of yum-config-manager (Michael Mraka)
- repoquery: Added --file switch to show who owns the given file (RhBug:1196952) (Parag Nemade)
- debuginfo-install: accept packages names specified as NEVRA (RhBug:1171046) (Petr Spacek)
- repoquery: accept package names specified as NEVRA (RhBug:1179366) (Petr Spacek)
- download: fix typo in 'No source rpm definded' (Petr Spacek)
- download: accept package names ending with .src too (Petr Spacek)
- download: Do not disable user-enabled repos (thanks Spacekpe) (Jan Silhan)
- Add README to tests/ directory (Petr Spacek)
- AUTHORS: updated (Jan Silhan)
- download: fix package download on Python 3 (Petr Spacek)

* Tue Mar 10 2015 Jan Silhan <jsilhan@redhat.com> - 0.1.6-2
- man pages moved into dnf-plugins-core subpackage

* Fri Mar 6 2015 Jan Silhan <jsilhan@redhat.com> - 0.1.6-1
- fixed python(3)-dnf dependency in f23

* Thu Feb 5 2015 Jan Silhan <jsilhan@redhat.com> - 0.1.5-1
- updated package url (Michael Mraka)
- also dnf_version could be specified on rpmbuild commandline (Michael Mraka)
- simple script to build test package (Michael Mraka)
- let gitrev be specified on rpmbuild commandline (Michael Mraka)
- assign default GITREV value (Michael Mraka)
- standard way to find out latest commit (Michael Mraka)
- debuginfo-install: fix handling of subpackages with non-zero epoch (Petr Spacek)
- debuginfo-install: Make laywers happier by assigning copyright to Red Hat (Petr Spacek)
- debuginfo-install: remove dead code uncovered by variable renaming (Petr Spacek)
- debuginfo-install: clearly separate source and debug package names (Petr Spacek)
- debuginfo-install: use descriptive parameter name in _is_available() (Petr Spacek)
- repoquery: add -l option to list files contained in the package (Petr Spacek)
- 1187773 - replace undefined variable (Miroslav Suchý)
- download: fixed unicode location error (RhBug:1178239) (Jan Silhan)
- builddep recognizes nosrc.rpm pkgs (RhBug:1166126) (Jan Silhan)
- builddep: added nosignatures flag to rpm transaction set (Jan Silhan)
- builddep: more verbose output of non-matching packages (RhBug:1155211) (Jan Silhan)
- package: archive script is the same as in dnf (Jan Silhan)
- spec: exclude __pycache__ dir (Igor Gnatenko)

* Fri Dec 5 2014 Jan Silhan <jsilhan@redhat.com> - 0.1.4-1
- revert of commit 80ae3f4 (Jan Silhan)
- transifex update (Jan Silhan)
- spec: binded to current dnf version (Jan Silhan)
- generate_completion_cache: use sqlite instead of text files (Igor Gnatenko)
- logging: renamed log file (Related:RhBug:1074715) (Jan Silhan)
- Add reposync. (RhBug:1139738) (Ales Kozumplik)
- download: fix traceback if rpm package has no defined sourcerpm (RhBug: 1144003) (Tim Lauridsen)
- lint: ignore warnings of a test accessing protected attribute. (Ales Kozumplik)
- repoquery lint: logger is not used. (Ales Kozumplik)
- repoquery: support querying of weak deps. (Ales Kozumplik)
- needs_restarting: fix typo (Miroslav Suchý)
- copr: migrate copr plugin form urlgrabber to python-request (Miroslav Suchý)
- Add needs-restarting command. (Ales Kozumplik)

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
