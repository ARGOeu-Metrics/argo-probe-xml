%define underscore() %(echo %1 | sed 's/-/_/g')

Summary:       ARGO probe that checks the value of elements in given XML using XPath
Name:          argo-probe-xml
Version:       0.1.1
Release:       1%{?dist}
Source0:       %{name}-%{version}.tar.gz
License:       ASL 2.0
Group:         Development/System
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Prefix:        %{_prefix}
BuildArch:     noarch

BuildRequires: python3-devel
Requires: python36-requests
Requires: python36-lxml


%description
ARGO probe that checks the value of elements in given XML using XPath

%prep
%setup -q


%build
%{py3_build}


%install
%{py3_install "--record=INSTALLED_FILES" }


%clean
rm -rf $RPM_BUILD_ROOT


%files -f INSTALLED_FILES
%defattr(-,root,root)
%dir %{python3_sitelib}/%{underscore %{name}}/
%{python3_sitelib}/%{underscore %{name}}/*.py


%changelog
* Tue Sep 28 2022 Katarina Zailac <kzailac@srce.hr> - 0.1.1-1
- ARGO-3993 Improve XML probe to just check if the data is in the XML format
- ARGO-3957 Create generic XML probe

