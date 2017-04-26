%{?!dnf_lowest_compatible: %global dnf_lowest_compatible 2.4.0}
%{?!dnf_not_compatible: %global dnf_not_compatible 3.0}
%global dnf_plugins_extra 2.0.0
%global hawkey_version 0.7.0

%if 0%{?rhel} && 0%{?rhel} <= 7
%bcond_with python3
%else
%bcond_without python3
%endif

Name:           dnf-plugins-core
Version:        2.0.0
Release:        1%{?dist}
Summary:        Core Plugins for DNF
License:        GPLv2+
URL:            https://github.com/rpm-software-management/dnf-plugins-core
Source0:        %{url}/archive/%{name}-%{version}/%{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  cmake
BuildRequires:  gettext
%if %{with python3}
Requires:       python3-%{name} = %{version}-%{release}
%else
Requires:       python2-%{name} = %{version}-%{release}
%endif
Provides:       dnf-command(builddep)
Provides:       dnf-command(config-manager)
Provides:       dnf-command(copr)
Provides:       dnf-command(debug-dump)
Provides:       dnf-command(debug-restore)
Provides:       dnf-command(debuginfo-install)
Provides:       dnf-command(download)
Provides:       dnf-command(repoclosure)
Provides:       dnf-command(repograph)
Provides:       dnf-command(repomanage)
Provides:       dnf-command(reposync)
Provides:       dnf-plugins-extras-debug = %{version}-%{release}
Provides:       dnf-plugins-extras-repoclosure = %{version}-%{release}
Provides:       dnf-plugins-extras-repograph = %{version}-%{release}
Provides:       dnf-plugins-extras-repomanage = %{version}-%{release}
Provides:       dnf-plugin-builddep = %{version}-%{release}
Provides:       dnf-plugin-config-manager = %{version}-%{release}
Provides:       dnf-plugin-debuginfo-install = %{version}-%{release}
Provides:       dnf-plugin-download = %{version}-%{release}
Provides:       dnf-plugin-generate_completion_cache = %{version}-%{release}
Provides:       dnf-plugin-needs_restarting = %{version}-%{release}
Provides:       dnf-plugin-repoclosure = %{version}-%{release}
Provides:       dnf-plugin-repograph = %{version}-%{release}
Provides:       dnf-plugin-repomanage = %{version}-%{release}
Provides:       dnf-plugin-reposync = %{version}-%{release}
Conflicts:      dnf-plugins-extras-common-data < %{dnf_plugins_extra}

%description
Core Plugins for DNF. This package enhances DNF with builddep, config-manager, copr, debug,
debuginfo-install, download, needs-restarting, repoclosure, repograph, repomanage and reposync
commands. Additionally provides generate_completion_cache passive plugin.

%package -n python2-%{name}
Summary:        Core Plugins for DNF
%{?python_provide:%python_provide python2-%{name}}
BuildRequires:  python2-dnf >= %{dnf_lowest_compatible}
BuildRequires:  python2-dnf < %{dnf_not_compatible}
%if 0%{?rhel} && 0%{?rhel} <= 7
BuildRequires:  python-nose
%else
BuildRequires:  python2-nose
%endif
BuildRequires:  python-sphinx
BuildRequires:  python2-devel
Requires:       python2-dnf >= %{dnf_lowest_compatible}
Requires:       python2-dnf < %{dnf_not_compatible}
Requires:       python-hawkey >= %{hawkey_version}
Provides:       python2-dnf-plugins-extras-debug = %{version}-%{release}
Provides:       python2-dnf-plugins-extras-repoclosure = %{version}-%{release}
Provides:       python2-dnf-plugins-extras-repograph = %{version}-%{release}
Provides:       python2-dnf-plugins-extras-repomanage = %{version}-%{release}
Obsoletes:      python2-dnf-plugins-extras-debug < %{dnf_plugins_extra}
Obsoletes:      python2-dnf-plugins-extras-repoclosure < %{dnf_plugins_extra}
Obsoletes:      python2-dnf-plugins-extras-repograph < %{dnf_plugins_extra}
Obsoletes:      python2-dnf-plugins-extras-repomanage < %{dnf_plugins_extra}

Conflicts:      %{name} <= 0.1.5
# let the both python plugin versions be updated simultaneously
Conflicts:      python3-%{name} < %{version}-%{release}
Conflicts:      python-%{name} < %{version}-%{release}

%description -n python2-%{name}
Core Plugins for DNF, Python 2 interface. This package enhances DNF with builddep, config-manager,
copr, degug, debuginfo-install, download, needs-restarting, repoclosure, repograph, repomanage and
reposync commands. Additionally provides generate_completion_cache passive plugin.

%if %{with python3}
%package -n python3-%{name}
Summary:    Core Plugins for DNF
%{?python_provide:%python_provide python3-%{name}}
BuildRequires:  python3-devel
BuildRequires:  python3-dnf >= %{dnf_lowest_compatible}
BuildRequires:  python3-dnf < %{dnf_not_compatible}
BuildRequires:  python3-nose
BuildRequires:  python3-sphinx
Requires:       python3-dnf >= %{dnf_lowest_compatible}
Requires:       python3-dnf < %{dnf_not_compatible}
Requires:       python3-hawkey >= %{hawkey_version}
Conflicts:      %{name} <= 0.1.5
# let the both python plugin versions be updated simultaneously
Conflicts:      python2-%{name} < %{version}-%{release}
Conflicts:      python-%{name} < %{version}-%{release}
Provides:       python3-dnf-plugins-extras-debug = %{version}-%{release}
Provides:       python3-dnf-plugins-extras-repoclosure = %{version}-%{release}
Provides:       python3-dnf-plugins-extras-repograph = %{version}-%{release}
Provides:       python3-dnf-plugins-extras-repomanage = %{version}-%{release}
Obsoletes:      python3-dnf-plugins-extras-debug < %{dnf_plugins_extra}
Obsoletes:      python3-dnf-plugins-extras-repoclosure < %{dnf_plugins_extra}
Obsoletes:      python3-dnf-plugins-extras-repograph < %{dnf_plugins_extra}
Obsoletes:      python3-dnf-plugins-extras-repomanage < %{dnf_plugins_extra}

%description -n python3-%{name}
Core Plugins for DNF, Python 3 interface. This package enhances DNF with builddep, config-manager, 
copr, debug, debuginfo-install, download, needs-restarting, repoclosure, repograph, repomanage and
reposync commands. Additionally provides generate_completion_cache passive plugin.
%endif

%package -n python2-dnf-plugin-leaves
Summary:        Leaves Plugin for DNF
Requires:       python2-%{name} = %{version}-%{release}
Provides:       python2-dnf-plugins-extras-leaves = %{version}-%{release}
Provides:       dnf-command(leaves)
Provides:       dnf-plugin-leaves = %{version}-%{release}
Provides:       dnf-plugins-extras-leaves = %{version}-%{release}
Conflicts:      dnf-plugins-extras-common-data < %{dnf_plugins_extra}
Conflicts:      python3-dnf-plugin-leaves < %{version}-%{release}
Obsoletes:      python2-dnf-plugins-extras-leaves < %{dnf_plugins_extra}

%description -n python2-dnf-plugin-leaves
Leaves Plugin for DNF, Python 2 version. List all installed packages
not required by any other installed package.

%package -n python3-dnf-plugin-leaves
Summary:        Leaves Plugin for DNF
Requires:       python3-%{name} = %{version}-%{release}
Provides:       python3-dnf-plugins-extras-leaves = %{version}-%{release}
Provides:       dnf-command(leaves)
Provides:       dnf-plugin-leaves = %{version}-%{release}
Provides:       dnf-plugins-extras-leaves = %{version}-%{release}
Conflicts:      dnf-plugins-extras-common-data < %{dnf_plugins_extra}
Conflicts:      python2-dnf-plugin-leaves < %{version}-%{release}
Obsoletes:      python3-dnf-plugins-extras-leaves < %{dnf_plugins_extra}

%description -n python3-dnf-plugin-leaves
Leaves Plugin for DNF, Python 3 version. List all installed packages
not required by any other installed package.

%package -n python2-dnf-plugin-local
Summary:        Local Plugin for DNF
Requires:       %{_bindir}/createrepo_c
Requires:       python2-%{name} = %{version}-%{release}
Provides:       dnf-plugin-local =  %{version}-%{release}
Provides:       python2-dnf-plugins-extras-local = %{version}-%{release}
Provides:       dnf-plugins-extras-local = %{version}-%{release}
Conflicts:      dnf-plugins-extras-common-data < %{dnf_plugins_extra}
Conflicts:      python3-dnf-plugin-local < %{version}-%{release}
Obsoletes:      python2-dnf-plugins-extras-local < %{dnf_plugins_extra}

%description -n python2-dnf-plugin-local
Local Plugin for DNF, Python 2 version. Automatically copy all downloaded packages to a
repository on the local filesystem and generating repo metadata.

%package -n python3-dnf-plugin-local
Summary:        Local Plugin for DNF
Requires:       %{_bindir}/createrepo_c
Requires:       python3-%{name} = %{version}-%{release}
Provides:       dnf-plugin-local =  %{version}-%{release}
Provides:       python3-dnf-plugins-extras-local = %{version}-%{release}
Provides:       dnf-plugins-extras-local = %{version}-%{release}
Conflicts:      dnf-plugins-extras-common-data < %{dnf_plugins_extra}
Conflicts:      python2-dnf-plugin-local < %{version}-%{release}
Obsoletes:      python3-dnf-plugins-extras-local < %{dnf_plugins_extra}

%description -n python3-dnf-plugin-local
Local Plugin for DNF, Python 3 version. Automatically copy all downloaded
packages to a repository on the local filesystem and generating repo metadata.

%package -n python2-dnf-plugin-migrate
Summary:        Migrate Plugin for DNF
Requires:       python2-%{name} = %{version}-%{release}
Requires:       yum
Provides:       dnf-plugin-migrate = %{version}-%{release}
Provides:       python2-dnf-plugins-extras-migrate = %{version}-%{release}
Provides:       dnf-command(migrate)
Provides:       dnf-plugins-extras-migrate = %{version}-%{release}
Conflicts:      dnf-plugins-extras-common-data < %{dnf_plugins_extra}
Obsoletes:      python2-dnf-plugins-extras-migrate < %{dnf_plugins_extra}

%description -n python2-dnf-plugin-migrate
Migrate Plugin for DNF, Python 2 version. Migrates history, group and yumdb data from yum to dnf.

%package -n python2-dnf-plugin-show-leaves
Summary:        Leaves Plugin for DNF
Requires:       python2-%{name} = %{version}-%{release}
Requires:       python2-dnf-plugin-leaves = %{version}-%{release}
Provides:       dnf-plugin-show-leaves =  %{version}-%{release}
Provides:       python2-dnf-plugins-extras-show-leaves = %{version}-%{release}
Provides:       dnf-command(show-leaves)
Provides:       dnf-plugins-extras-show-leaves = %{version}-%{release}
Conflicts:      dnf-plugins-extras-common-data < %{dnf_plugins_extra}
Conflicts:      python3-dnf-plugin-show-leaves < %{version}-%{release}
Obsoletes:      python2-dnf-plugins-extras-show-leaves < %{dnf_plugins_extra}

%description -n python2-dnf-plugin-show-leaves
Show-leaves Plugin for DNF, Python 2 version. List all installed
packages that are no longer required by any other installed package
after a transaction.

%package -n python3-dnf-plugin-show-leaves
Summary:        Show-leaves Plugin for DNF
Requires:       python3-%{name} = %{version}-%{release}
Requires:       python3-dnf-plugin-leaves = %{version}-%{release}
Provides:       dnf-plugin-show-leaves =  %{version}-%{release}
Provides:       python3-dnf-plugins-extras-show-leaves = %{version}-%{release}
Provides:       dnf-command(show-leaves)
Provides:       dnf-plugins-extras-show-leaves = %{version}-%{release}
Conflicts:      dnf-plugins-extras-common-data < %{dnf_plugins_extra}
Conflicts:      python2-dnf-plugin-show-leaves < %{version}-%{release}
Obsoletes:      python3-dnf-plugins-extras-show-leaves < %{dnf_plugins_extra}

%description -n python3-dnf-plugin-show-leaves
Show-leaves Plugin for DNF, Python 3 version. List all installed
packages that are no longer required by any other installed package
after a transaction.

%package -n python2-dnf-plugin-versionlock
Summary:        Version Lock Plugin for DNF
Requires:       python2-%{name} = %{version}-%{release}
Provides:       dnf-plugin-versionlock =  %{version}-%{release}
Provides:       python2-dnf-plugins-extras-versionlock = %{version}-%{release}
Provides:       dnf-command(versionlock)
Provides:       dnf-plugins-extras-versionlock = %{version}-%{release}
Conflicts:      dnf-plugins-extras-common-data < %{dnf_plugins_extra}
Conflicts:      python3-dnf-plugin-versionlock < %{version}-%{release}
Obsoletes:      python2-dnf-plugins-extras-versionlock < %{dnf_plugins_extra}

%description -n python2-dnf-plugin-versionlock
Version lock plugin takes a set of name/versions for packages and excludes all other
versions of those packages. This allows you to e.g. protect packages from being
updated by newer versions.

%package -n python3-dnf-plugin-versionlock
Summary:        Version Lock Plugin for DNF
Requires:       python3-%{name} = %{version}-%{release}
Provides:       dnf-plugin-versionlock =  %{version}-%{release}
Provides:       python3-dnf-plugins-extras-versionlock = %{version}-%{release}
Provides:       dnf-command(versionlock)
Provides:       dnf-plugins-extras-versionlock = %{version}-%{release}
Conflicts:      dnf-plugins-extras-common-data < %{dnf_plugins_extra}
Conflicts:      python2-dnf-plugin-versionlock < %{version}-%{release}
Obsoletes:      python3-dnf-plugins-extras-versionlock < %{dnf_plugins_extra}

%description -n python3-dnf-plugin-versionlock
Version lock plugin takes a set of name/versions for packages and excludes all other
versions of those packages. This allows you to e.g. protect packages from being
updated by newer versions.

%prep
%autosetup
mkdir build-py2
%if %{with python3}
mkdir build-py3
%endif

%build
pushd build-py2
  %cmake ../
  %make_build
  make doc-man
popd
%if %{with python3}
pushd build-py3
  %cmake ../ -DPYTHON_DESIRED:str=3
  %make_build
  make doc-man
popd
%endif

%install
pushd build-py2
  %make_install
popd
%if %{with python3}
pushd build-py3
  %make_install
popd
%endif
%find_lang %{name}

%check
PYTHONPATH=./plugins nosetests-%{python2_version} -s tests/
%if %{with python3}
PYTHONPATH=./plugins nosetests-%{python3_version} -s tests/
%endif

%files
%{_mandir}/man8/dnf.plugin.builddep.*
%{_mandir}/man8/dnf.plugin.config_manager.*
%{_mandir}/man8/dnf.plugin.copr.*
%{_mandir}/man8/dnf.plugin.debug.*
%{_mandir}/man8/dnf.plugin.debuginfo-install.*
%{_mandir}/man8/dnf.plugin.download.*
%{_mandir}/man8/dnf.plugin.generate_completion_cache.*
%{_mandir}/man8/dnf.plugin.needs_restarting.*
%{_mandir}/man8/dnf.plugin.repoclosure.*
%{_mandir}/man8/dnf.plugin.repograph.*
%{_mandir}/man8/dnf.plugin.repomanage.*
%{_mandir}/man8/dnf.plugin.reposync.*

%files -n python2-%{name} -f %{name}.lang
%license COPYING
%doc AUTHORS README.rst
%ghost %{_var}/cache/dnf/packages.db
%config(noreplace) %{_sysconfdir}/dnf/plugins/debuginfo-install.conf
%{python2_sitelib}/dnf-plugins/builddep.*
%{python2_sitelib}/dnf-plugins/config_manager.*
%{python2_sitelib}/dnf-plugins/copr.*
%{python2_sitelib}/dnf-plugins/debug.*
%{python2_sitelib}/dnf-plugins/debuginfo-install.*
%{python2_sitelib}/dnf-plugins/download.*
%{python2_sitelib}/dnf-plugins/generate_completion_cache.*
%{python2_sitelib}/dnf-plugins/needs_restarting.*
%{python2_sitelib}/dnf-plugins/repoclosure.*
%{python2_sitelib}/dnf-plugins/repograph.*
%{python2_sitelib}/dnf-plugins/repomanage.*
%{python2_sitelib}/dnf-plugins/reposync.*
%{python2_sitelib}/dnfpluginscore/

%if %{with python3}
%files -n python3-%{name} -f %{name}.lang
%license COPYING
%doc AUTHORS README.rst
%ghost %{_var}/cache/dnf/packages.db
%config(noreplace) %{_sysconfdir}/dnf/plugins/debuginfo-install.conf
%{python3_sitelib}/dnf-plugins/builddep.py
%{python3_sitelib}/dnf-plugins/config_manager.py
%{python3_sitelib}/dnf-plugins/copr.py
%{python3_sitelib}/dnf-plugins/debug.py
%{python3_sitelib}/dnf-plugins/debuginfo-install.py
%{python3_sitelib}/dnf-plugins/download.py
%{python3_sitelib}/dnf-plugins/generate_completion_cache.py
%{python3_sitelib}/dnf-plugins/needs_restarting.py
%{python3_sitelib}/dnf-plugins/repoclosure.py
%{python3_sitelib}/dnf-plugins/repograph.py
%{python3_sitelib}/dnf-plugins/repomanage.py
%{python3_sitelib}/dnf-plugins/reposync.py
%{python3_sitelib}/dnf-plugins/__pycache__/builddep.*
%{python3_sitelib}/dnf-plugins/__pycache__/config_manager.*
%{python3_sitelib}/dnf-plugins/__pycache__/copr.*
%{python3_sitelib}/dnf-plugins/__pycache__/debug.*
%{python3_sitelib}/dnf-plugins/__pycache__/debuginfo-install.*
%{python3_sitelib}/dnf-plugins/__pycache__/download.*
%{python3_sitelib}/dnf-plugins/__pycache__/generate_completion_cache.*
%{python3_sitelib}/dnf-plugins/__pycache__/needs_restarting.*
%{python3_sitelib}/dnf-plugins/__pycache__/repoclosure.*
%{python3_sitelib}/dnf-plugins/__pycache__/repograph.*
%{python3_sitelib}/dnf-plugins/__pycache__/repomanage.*
%{python3_sitelib}/dnf-plugins/__pycache__/reposync.*
%{python3_sitelib}/dnfpluginscore/
%endif

%files -n python2-dnf-plugin-leaves
%{python2_sitelib}/dnf-plugins/leaves.*
%{_mandir}/man8/dnf.plugin.leaves.*

%files -n python3-dnf-plugin-leaves
%{python3_sitelib}/dnf-plugins/leaves.*
%{python3_sitelib}/dnf-plugins/__pycache__/leaves.*
%{_mandir}/man8/dnf.plugin.leaves.*

%files -n python2-dnf-plugin-local
%config(noreplace) %{_sysconfdir}/dnf/plugins/local.conf
%{python2_sitelib}/dnf-plugins/local.*
%{_mandir}/man8/dnf.plugin.local.*

%files -n python3-dnf-plugin-local
%config(noreplace) %{_sysconfdir}/dnf/plugins/local.conf
%{python3_sitelib}/dnf-plugins/local.*
%{python3_sitelib}/dnf-plugins/__pycache__/local.*
%{_mandir}/man8/dnf.plugin.local.*

%files -n python2-dnf-plugin-migrate
%{python2_sitelib}/dnf-plugins/migrate.*
%{_mandir}/man8/dnf.plugin.migrate.*

%files -n python2-dnf-plugin-show-leaves
%{python2_sitelib}/dnf-plugins/show_leaves.*
%{_mandir}/man8/dnf.plugin.show-leaves.*

%files -n python3-dnf-plugin-show-leaves
%{python3_sitelib}/dnf-plugins/show_leaves.*
%{python3_sitelib}/dnf-plugins/__pycache__/show_leaves.*
%{_mandir}/man8/dnf.plugin.show-leaves.*

%files -n python2-dnf-plugin-versionlock
%config(noreplace) %{_sysconfdir}/dnf/plugins/versionlock.conf
%config(noreplace) %{_sysconfdir}/dnf/plugins/versionlock.list
%{python2_sitelib}/dnf-plugins/versionlock.*
%{_mandir}/man8/dnf.plugin.versionlock.*

%files -n python3-dnf-plugin-versionlock
%config(noreplace) %{_sysconfdir}/dnf/plugins/versionlock.conf
%config(noreplace) %{_sysconfdir}/dnf/plugins/versionlock.list
%{python3_sitelib}/dnf-plugins/versionlock.*
%{python3_sitelib}/dnf-plugins/__pycache__/versionlock.*
%{_mandir}/man8/dnf.plugin.versionlock.*

%changelog
* Tue Mar 21 2017 Igor Gnatenko <ignatenko@redhat.com> 1.1.0-1
- dnf dowload --resolve should download everytime requested packages
  (RhBug:1276611) (stepasm)
- builddep: install requirements by provides (RhBug:1332830) (Igor Gnatenko)
- builddep: do not check GPG key of SRPM (RhBug:1431486) (Igor Gnatenko)
- builddep: properly check for nosrc.rpm (Igor Gnatenko)
- po: Update translations (RhBug:1429087) (Igor Gnatenko)
- Remove noroot plugin that was move into dnf itself (Jaroslav Mracek)

* Mon Feb 20 2017 Jaroslav Mracek <jmracek@redhat.com> 1.0.2-1
- bump version to 1.0.2 + update release notes (Jaroslav Mracek)
- download: add --urlprotocols option (Dusty Mabe)
- download: add --url cli option (RhBug:1250115) (Dusty Mabe)
- download: refactor download code (Dusty Mabe)
- copr: Tweak wording to be more generic (Neal Gompa)
- Automatic commit of package [dnf-plugins-core] release [1.0.1-1]. (Jaroslav
  Mracek)
- bump version to 1.0.1 + update release notes (Jaroslav Mracek)

* Thu Feb 09 2017 Jaroslav Mracek <jmracek@redhat.com> 1.0.1-1
- bump version to 1.0.1 + update release notes (Jaroslav Mracek)
- setup SideCI to ignore some PEP8 violations (Jaroslav Mracek)
- spec: define all configs as (noreplace) (Igor Gnatenko)
- spec: include __pycache__ files (Igor Gnatenko)
- builddep: print errors from RPM SPEC parser (Petr Spacek)

* Thu Sep 29 2016 Michal Luscon <mluscon@redhat.com> 1.0.0-0.rc1.1
- doc: open rpmspec in utf-8 mode (Igor Gnatenko)
- cls.chroot_config inside _guess_chroot returns None (RhBug: 1361003) (Michael
  Goodwin)
- builddep: adjust to new config (dnf-2.0) (Michal Luscon)
- Change minimal required version (Jaroslav Mracek)
- introduced config-manager --dump-variables (RhBug:1360752) (Michael Mraka)
- Fix string puzzle in translatable message (Luigi Toscano)
- Added alias to 'builddep'->'build-dep' (RhBug:1350604) (stepasm)
- reposync should keep packages (RhBug:1325350) (Michael Mraka)
- Change usage of add_remote_rpm according to new API (Jaroslav Mracek)
- Remove lib.py from plugins-core (Jaroslav Mracek)
- Delete repoquery from dnf-plugins-core (Jaroslav Mracek)
- removed protected_packages plugin (Jan Silhan)
- repoquery: add --requires-pre switch (RhBug:1303117) (Michal Luscon)
- spec: bump version to 1.0.0 (Igor Gnatenko)
- Automatic commit of package [dnf-plugins-core] release [0.1.21-2]. (Igor
  Gnatenko)
- Automatic commit of package [dnf-plugins-core] release [0.1.21-1]. (Igor
  Gnatenko)
- spec: explicitly conflict with python-%%{name} with different version (Igor
  Gnatenko)
- updated plugin to read_config() change (RhBug:1193823) (Michael Mraka)
- repoquery: sourcerpm does not contain epoch (RhBug:1335959) (Michael Mraka)
- enforce-api: use api method transaction (Michal Luscon)
- enforce-api: apply changes from Base class (Michal Luscon)
- copr: Read the %%distro_arch macro to determine Mageia chroot arch (Neal
  Gompa (ニール・ゴンパ))
- copr: Remove unnecessary function calls/options and simplify conditional
  (Neal Gompa (ニール・ゴンパ))
- copr: Add Mageia chroot selection support (Neal Gompa (ニール・ゴンパ))
- copr: Simplify and fix up reading copr chroot config override (Neal Gompa
  (ニール・ゴンパ))
- autoglob feature has been moved to filter() (RhBug:1279538) (Michael Mraka)

* Fri May 27 2016 Igor Gnatenko <ignatenko@redhat.com> 0.1.21-2
- spec: explicitly conflict with python-%%{name} with different version (Igor
  Gnatenko)

* Thu May 19 2016 Igor Gnatenko <ignatenko@redhat.com> 0.1.21-1
- doc: release notes 0.1.21 (Igor Gnatenko)
- spec: correctly set up requirements for python subpkg (Igor Gnatenko)
- spec: improve python packaging according to new guidelines & compat with EL7
  (Igor Gnatenko)
- tests/support: set priority and cost in RepoStub (Igor Gnatenko)
- repoquery: sourcerpm does not contain epoch (RhBug:1335959) (Michael Mraka)
- enforce-api: use api method transaction (Michal Luscon)
- enforce-api: apply changes from Base class (Michal Luscon)
- copr: Read the %%distro_arch macro to determine Mageia chroot arch (Neal
  Gompa (ニール・ゴンパ))
- copr: Remove unnecessary function calls/options and simplify conditional
  (Neal Gompa (ニール・ゴンパ))
- copr: Add Mageia chroot selection support (Neal Gompa (ニール・ゴンパ))
- copr: Simplify and fix up reading copr chroot config override (Neal Gompa
  (ニール・ゴンパ))
- zanata update (Jan Silhan)
- Add link for other project documentation pages (Jaroslav Mracek)
- autoglob feature has been moved to filter() (RhBug:1279538) (Michael Mraka)
- support globs in --what<weak_dep> (RhBug:1303311) (Michael Mraka)
- repoquery: fix typo (there -> that, and plural form) (Luigi Toscano)
- copr: fix string - singular is required (Luigi Toscano)
- doc: release notes updated to vallid plugins version (Jan Šilhan)

* Tue Apr 05 2016 Michal Luscon <mluscon@redhat.com> 0.1.20-1
- doc: release notes 0.1.20 (Igor Gnatenko)
- copr: Properly detect reposdir and add chroot override capability (Neal Gompa
  (ニール・ゴンパ))
- config_manager: Use new API in dnfpluginscore.lib for determining reposdir
  (Neal Gompa (ニール・ゴンパ))
- dnfpluginscore.lib: Add get_reposdir() API function (Neal Gompa (ニール・ゴンパ))
- Fix typo (Eduardo Mayorga Téllez)

* Tue Mar 22 2016 Miroslav Suchý <msuchy@redhat.com> 0.1.19-1
- spec: correct requires on F22 + EPEL (Miroslav Suchý)

* Tue Mar 22 2016 Miroslav Suchý <msuchy@redhat.com> 0.1.18-1
- Add myself as contributor in AUTHORS (Neal Gompa (ニール・ゴンパ))
- copr: copr.fedoraproject.org -> copr.fedorainfracloud.org (Neal Gompa
  (ニール・ゴンパ))
- copr: fix traceback when trying to enable non-existing project (RhBug:
  1304615) (Jakub Kadlčík)
- README: mention translation fixes should be made on Zanata (Jan Šilhan)

* Thu Feb 25 2016 Michal Luscon <mluscon@redhat.com> 0.1.17-1
- enable debuginfo repos if autoupdate is on (RhBug:1024701) (Michael Mraka)
- fixed string suffix removal (Michael Mraka)
- install latest debuginfo by default (Michael Mraka)
- Enable strings for translation (RhBug:1302214) (Parag Nemade)

* Mon Jan 25 2016 Jan Silhan <jsilhan@redhat.com> 0.1.16-1
- zanata update (Jan Silhan)
- AUTHORS: updated (Jan Silhan)
- run noroot in non cli mode (RhBug:1297511) (Jan Silhan)
- Sanitize repos containing a tilde in the URL (François RIGAULT)
- contributor added (clime)
- latest-limit option moved to base set of options making it compatible with
  --queryformat and other output formatters (RhBug: 1292475) (clime)
- builddep: do not download source package (Jeff Smith)
- repoquery: keep --autoremove as secret option (Jan Silhan)
- cosmetic: repoquery: remove unused imports (Jan Silhan)
- doc: repoquery: --recent (Jan Silhan)
- doc: renamed autoremove to unneeded and extended docs (Jan Silhan)

* Fri Dec 18 2015 Michal Luscon <mluscon@redhat.com> 0.1.15-1
- Make it possible to specify the source package name as parameter in stub
  constructor. (Alexander Todorov)
- Add --debuginfo to download (Alexander Todorov)
- resolve local RPMs when downloading. useful with --source (Alexander Todorov)
- spec: ensure python*-dnf-plugins-core versions are the same (RhBug:1283448)
  (Jan Silhan)
- reimplemented config file writing (RhBug:1253237) (Michael Mraka)

* Mon Nov 16 2015 Michal Luscon <mluscon@redhat.com> 0.1.14-1
- zanata update (Jan Silhan)
- repoquery: do not require loading metadata when we want to query system only
  (Jan Silhan)
- repoquery: fix unicode tracebacks (Michal Luscon)
- repoquery: use new methods recent, extras, unneeded (Michal Luscon)
- repoquery: use new api methods duplicated and latest (RhBug:1231572) (Michal
  Luscon)
- Exit with non-zero status if strict and package not found (alde)
- Fix cmdline conversion to unicode (RhBug:1265210) (Michal Domonkos)
- Remove extra 'l' in test class name (Alexander Todorov)
- copr: PEP formating (Miroslav Suchý)
- copr: allow to use staging instance of Copr for testing (Miroslav Suchý)
- do not use @ in repoid (RhBug:1280416) (Miroslav Suchý)
- reverts unintentional releaser from e035152 (Jan Silhan)
- don't look for builddeps on source packages (RhBug:1272936) (Michael Mraka)
- Fix hawkey version constraint (Neal Gompa (ニール・ゴンパ))

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
