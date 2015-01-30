Summary: tour package
Name: tour
Version: 4
Release: 6
Group: Utilities
License: GPLv2+
Distribution: DNF Core Plugins Test Suite.
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-hawkey
Packager: roll up <roll@up.net>
BuildRequires: emacs-extras
BuildRequires: emacs-goodies >= 100
%if 0%{?enable_optional_module}
BuildRequires: emacs-module
%endif

%description
The tour package to test stuff.

%prep

%build

%install

%files
