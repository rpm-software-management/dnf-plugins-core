%global gitrev bca8630
%global dnf_version 0.4.10-2
%global pluginspath /usr/share/dnf/plugins

Name:		dnf-plugins-core
Version:	0.0.5
Release:	2%{?dist}
Summary:	Core Plugins for DNF
Group:		System Environment/Base
License:	GPLv2+
URL:		https://github.com/akozumpl/dnf-plugins-core
Source0:	http://akozumpl.fedorapeople.org/dnf-plugins-core-%{gitrev}.tar.xz
BuildArch:	noarch
BuildRequires:	dnf >= %{dnf_version}
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

%build

%prep
%setup -q -n dnf-plugins-core

%install
%global py2dir %{python_sitelib}/dnf-plugins
%global py3dir %{python3_sitelib}/dnf-plugins

mkdir -p %{buildroot}/%{py2dir}
cp -a plugins/builddep.py %{buildroot}/%{py2dir}
cp -a plugins/debuginfo-install.py %{buildroot}/%{py2dir}
cp -a plugins/generate_completion_cache.py %{buildroot}/%{py2dir}
cp -a plugins/kickstart.py %{buildroot}/%{py2dir}
cp -a plugins/noroot.py %{buildroot}/%{py2dir}

mkdir -p %{buildroot}/%{py3dir}
cp -a plugins/builddep.py %{buildroot}/%{py3dir}
cp -a plugins/debuginfo-install.py %{buildroot}/%{py3dir}
cp -a plugins/generate_completion_cache.py %{buildroot}/%{py3dir}
cp -a plugins/noroot.py %{buildroot}/%{py3dir}

%check

PYTHONPATH=./plugins nosetests-2.7 -s tests/
PYTHONPATH=./plugins nosetests-3.3 -s tests/

%files
%doc AUTHORS COPYING README.rst
%{py2dir}/*

%files -n python3-dnf-plugins-core
%doc AUTHORS COPYING README.rst
%{py3dir}/*

%changelog
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
