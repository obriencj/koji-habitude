%global srcname koji-habitude
%global server 0.1.0
%global srcrel 0
%global dstname koji_habitude
%global sum Synchronizes local koji data expectations with a hub instance


Name:           %{srcname}
Version:        0.1.0
Release:        %{srcrel}%{?dist}
Summary:        %{sum}

License:        GPL-3.0-or-later
URL:            https://github.com/obriencj/koji-habitude
Source0:        %{srcname}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-pip
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel


%description
koji-habitude is a configuration management tool for Koji build systems.
It provides a declarative approach to managing koji objects through YAML
templates and data files, with intelligent dependency resolution and tiered
execution.


%prep
%autosetup -n %{srcname}-%{version}


%build
%py3_build_wheel


%install
%py3_install_wheel  %{dstname}-%{version}-py3-none-any.whl


%package -n python3-%{srcname}
Summary: %{sum}


# Runtime dependencies
Requires:       python3-click
Requires:       python3-koji
Requires:       python3-pyyaml
Requires:       python3-jinja2
Requires:       python3-pydantic


%{?python_provide:%python_provide python3-%{srcname}}
%{?py_provides:%py_provides python3-%{srcname}}


%files
%license LICENSE
%doc README.md
%{python3_sitelib}/%{dstname}/
%{python3_sitelib}/%{dstname}-%{version}.dist-info/
%{_bindir}/koji-habitude


%changelog
* Mon Oct 13 2025 Christopher O'Brien <obriencj@gmail.com> - 0.1.0-1
- Initial RPM package for koji-habitude
- Provides CLI tool for declarative koji configuration management
