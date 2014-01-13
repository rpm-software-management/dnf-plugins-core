%global gitrev eb97d01
%global dnf_version 0.4.10-2
%global pluginspath /usr/share/dnf/plugins

Name:		dnf-plugins-core
Version:	0.0.2
Release:	1%{?dist}
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
cp -a plugins/kickstart.py %{buildroot}/%{py2dir}
cp -a plugins/noroot.py %{buildroot}/%{py2dir}

mkdir -p %{buildroot}/%{py3dir}
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
