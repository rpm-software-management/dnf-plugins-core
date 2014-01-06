%global gitrev 561c107
%global dnf_version 0.4.10-2
%global pluginspath /usr/share/dnf/plugins

Name:		dnf-plugins-core
Version:	0.0.1
Release:	4%{?dist}
Summary:	Core Plugins for DNF
Group:		System Environment/Base
License:	GPLv2+
URL:		https://github.com/akozumpl/dnf-plugins-core
Source0:	http://akozumpl.fedorapeople.org/dnf-plugins-core-%{gitrev}.tar.xz
BuildArch:	noarch
BuildRequires:	python2-devel
Requires:	dnf >= %{dnf_version}
Requires:	pykickstart

%description
Core Plugins for DNF.

%build

%prep
%setup -q -n dnf-plugins-core

%install
%global py2dir %{python_sitelib}/dnf-plugins

mkdir -p %{buildroot}/%{py2dir}
cp -a plugins/noroot.py %{buildroot}/%{py2dir}

%check

%files
%doc AUTHORS COPYING README.rst
%{py2dir}/*

%changelog
* Wed Jan 8 2014 Cristian Ciupitu <cristian.ciupitu@yahoo.com> - 0.0.1-4
- Spec updates.

* Tue Jan 7 2014 Aleš Kozumplík <ales@redhat.com> - 0.0.1-3
- Spec updates.

* Mon Jan 6 2014 Aleš Kozumplík <ales@redhat.com> - 0.0.1-2
- Spec updates.

* Fri Dec 20 2013 Aleš Kozumplík <ales@redhat.com> - 0.0.1-1
- The initial package version.
