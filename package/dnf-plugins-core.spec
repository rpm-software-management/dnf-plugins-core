%global gitrev 6e058c1
%global dnf_version 0.4.9
%global pluginspath /usr/share/dnf/plugins

Name:		dnf-plugins-core
Version:	0.0.1
Release:	1%{?dist}
Summary:	Core Plugins for DNF
Group:		System Environment/Base
License:	GPLv2+
URL:		https://github.com/akozumpl/dnf-plugins
Source0:	http://akozumpl.fedorapeople.org/dnf-plugins-core-%{gitrev}.tar.xz
BuildArch:	noarch
BuildRequires:	dnf >= %{dnf_version}
BuildRequires:	python-nose
BuildRequires:	python2-devel
Requires:	dnf >= %{dnf_version}

%description
Core Plugins for DNF.

%prep
%setup -q -n dnf-plugins

%install
%global py2dir %{python_sitelib}/dnf-plugins

mkdir -p $RPM_BUILD_ROOT/%{py2dir}
cp plugins/noroot.py $RPM_BUILD_ROOT%{py2dir}

%check

PYTHONPATH=./plugins nosetests-2.7 -s tests/

%files
%doc AUTHORS COPYING README.rst
%{py2dir}/*

%changelog

* Fri Dec 20 2013 Aleš Kozumplík <ales@redhat.com> - 0.0.1-1
- The initial package version.
