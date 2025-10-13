%global srcname koji-habitude
%global dstname koji_habitude
%global sum Synchronizes local koji data expectations with a hub instance


Name:           python3-%{srcname}
Version:        0.1.0
Release:        1%{?dist}
Summary:        %{sum}

License:        GPL-3.0-or-later
URL:            https://github.com/obriencj/koji-habitude
Source0:        %{srcname}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel

# Runtime dependencies
Requires:       python3-click
Requires:       python3-koji
Requires:       python3-pyyaml
Requires:       python3-jinja2
Requires:       python3-pydantic

%{?python_provide:%python_provide python3-%{srcname}}
%{?py_provides:%py_provides python3-%{srcname}}


%description
koji-habitude is a configuration management tool for Koji build systems.
It provides a declarative approach to managing koji objects through YAML
templates and data files, with intelligent dependency resolution and tiered
execution.

Key Features:
- Define koji objects (tags, external repos, users, targets, hosts, groups,
  channels, permissions, build types, archive types) in YAML
- Use Jinja2 templates for dynamic configuration generation
- Automatically resolve dependencies between objects
- Preview template expansion results
- Apply changes in the correct order through tiered execution
- Validate configurations offline before deployment


%prep
%autosetup -n %{srcname}-%{version}


%build
%py3_build_wheel


%install
%py3_install_wheel  %{dstname}-%{version}-py3-none-any.whl


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
