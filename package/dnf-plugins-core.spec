%global gitrev 68a05e0
%global dnf_version 0.5.0

Name:		dnf-plugins-core
Version:	0.0.6
Release:	1%{?dist}
Summary:	Core Plugins for DNF
Group:		System Environment/Base
License:	GPLv2+
URL:		https://github.com/akozumpl/dnf-plugins-core

# source archive is created by running package/archive from a git checkout
Source0:	dnf-plugins-core-%{gitrev}.tar.xz

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


%prep
%setup -q -n dnf-plugins-core
rm -rf py3
mkdir ../py3
cp -a . ../py3/
mv ../py3 ./

%build
%cmake .
make %{?_smp_mflags}
pushd py3
%cmake -DPYTHON_DESIRED:str=3 .
make %{?_smp_mflags}
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

%files -n python3-dnf-plugins-core -f %{name}.lang
%doc AUTHORS COPYING README.rst
%{python3_sitelib}/dnf-plugins/*
%{python3_sitelib}/dnfpluginscore/

%changelog
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
