%global srcname koji-habitude
%global srcver 0.9.1
%global srcrel 0
%global dstname koji_habitude
%global sum Synchronizes local koji data expectations with a hub instance

# we don't generate binaries, let's turn that part off
%global debug_package %{nil}

# we'll build on RHEL/Rocky/Alma 8, but we need to use the python39 module
%if 0%{?rhel} && 0%{?rhel} <= 8
%global pythree python39
%else
%global pythree python3
%endif


Name:           %{srcname}
Version:        %{srcver}
Release:        %{srcrel}%{?dist}
Summary:        %{sum}

License:        GPL-3.0-or-later
URL:            https://github.com/obriencj/koji-habitude
Source0:        %{srcname}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  %{pythree}-devel
BuildRequires:  %{pythree}-pip
BuildRequires:  %{pythree}-setuptools
BuildRequires:  %{pythree}-wheel

%if 0%{?rhel} && 0%{?rhel} <= 8
BuildRequires:  python39-rpm-macros
%endif


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


%package -n %{pythree}-%{srcname}
Summary: %{sum}

# Runtime dependencies
Requires:       %{pythree}-click
Requires:       %{pythree}-koji
Requires:       %{pythree}-pyyaml
Requires:       %{pythree}-jinja2
Requires:       %{pythree}-pydantic

%if 0%{?rhel} && 0%{?rhel} <= 8
%{?py_provides:%py_provides %{srcname}}
%else
%{?python_provide:%python_provide %{pythree}-%{srcname}}
%{?py_provides:%py_provides %{srcname}}
%endif


%description -n %{pythree}-%{srcname}
koji-habitude is a configuration management tool for Koji build systems.
It provides a declarative approach to managing koji objects through YAML
templates and data files, with intelligent dependency resolution and tiered
execution.


%files -n %{pythree}-%{srcname}
%license LICENSE
%doc README.md
%{python3_sitelib}/%{dstname}/
%{python3_sitelib}/%{dstname}-%{version}.dist-info/
%{_bindir}/koji-habitude


%changelog
* Mon Dec 29 2025 Christopher O'Brien <obriencj@gmail.com> - 0.9.0-1
- See the 0.9.0 release notes for a list of initial features

* Mon Oct 13 2025 Christopher O'Brien <obriencj@gmail.com> - 0.1.0-1
- Initial RPM package for koji-habitude
- Provides CLI tool for declarative koji configuration management
