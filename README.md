# koji-habitude

> **⚠️ Work In Progress**: This project is currently under development. Core
> architecture is largely complete including CLI framework, data models, and
> dependency resolution, but synchronization with Koji hubs is not yet
> implemented.

## Current Status

**✅ Completed:**
- CLI framework with all commands (`sync`, `diff`, `validate`, `expand`,
  `list-templates`)
- Comprehensive data models for all Koji object types (8 CORE_MODELS)
- Pydantic validation with field constraints and proper error handling
- Dependency resolution architecture (Resolver and Solver modules)
- Tiered execution system with automatic splitting for cross-dependencies
- Comprehensive unit test coverage (274 tests across 8 test files)
- Template expansion and YAML processing

**🚧 In Progress:**
- Koji client integration for actual synchronization
- Object diffing logic implementation
- Multicall support for efficient Koji operations

**📋 Next Steps:**
- Implement `sync` and `validate` command bodies
- Add CLI testing (currently missing test_cli.py)
- Performance optimization and error handling improvements


## Overview

koji-habitude is a configuration management tool for
[Koji](https://pagure.io/koji) build systems. It provides a declarative approach
to managing koji objects through YAML templates and data files, with intelligent
dependency resolution and tiered execution.


The tool synchronizes local koji data expectations with a hub instance, allowing
you to:
- Define koji objects (tags, external repos, users, targets, hosts, groups) in
  YAML
- Use Jinja2 templates for dynamic configuration generation
- Automatically resolve dependencies between objects (tag inheritance)
- Preview template expansion results with the `expand` command
- Apply changes in the correct order through tiered execution
- Validate configurations offline before deployment

This project is an offshoot of [koji-box](https://github.com/obriencj/koji-box),
fulfilling the need for populating a boxed koji instance with a bunch of tags
and targets. However it is being written such that it can be used with any koji
instance, in the hopes that it may bring joy into the lives of those trying to
keep projects packagers happy.


## CLI

koji-habitude is built using [Click](https://click.palletsprojects.com/) and
provides four main commands:


### Synchronize with Koji Hub

```bash
koji-habitude sync [OPTIONS] DATA [DATA...]
```

**Options:**
- `DATA`: directories or files to work with
- `--templates PATH`: location to find templates that are not available in
  `DATA`
- `--profile PROFILE`: Koji profile to use for connection (optional)
- `--offline`: Run in offline mode (no koji connection)
- `--dry-run`: Show what would be done without making changes

```bash
koji-habitude diff [OPTIONS] DATA [DATA...]
```

A convenience alias for `koji-habitude sync --dry-run`

### List Available Templates

```bash
koji-habitude list-templates [OPTIONS] PATH [PATH...]
```

Shows all templates found in the given locations with their configuration
details.


### Validate Configuration

```bash
koji-habitude validate [OPTIONS] DATA [DATA...]
```

Validates templates and data files without connecting to koji, checking for:
- Template syntax and structure
- Circular dependencies
- Missing dependencies
- Data consistency


### Expand Templates and Data

```bash
koji-habitude expand [OPTIONS] DATA [DATA...]
```

**Options:**
- `DATA`: directories or files to work with
- `--templates PATH`: location to find templates that are not available in
  `DATA`
- `--profile PROFILE`: Koji profile to use for connection (optional)
- `--offline`: Run in offline mode (no koji connection)

Expands templates and data files into final YAML output. This command loads
templates from the specified locations, processes the data files through
template expansion, and outputs the final YAML content to stdout. Useful for
previewing the results of template expansion before applying changes.


## YAML Format

The yaml files can be single or multi-document. Documents are processed
in-order. Each document has 'type' key, which indicates the document type. The
default available types are 'template', 'tag', 'target', 'user', 'group',
'host', and 'external-repo'. Templates define new types, based on the name of
the template.


## Templates

Templates use [Jinja2](https://jinja.palletsprojects.com/) for dynamic content
generation. Each template is defined in YAML with the following structure:

```yaml
---
type: template
name: my-template
content: |
  ---
  type: tag
  name: {{ name }}
  inheritance:
    {% for parent in parents %}
    - parent: {{ parent }}
      priority: {{ loop.index * 10 }}
    {% endfor %}
schema:
  # Optional schema validation (future feature)
```

Templates can also reference external Jinja2 files:

```yaml
---
type: template
name: my-template
file: my-template.j2
schema:
  # Optional schema validation
```


### Template Expansion

When processing data files, objects with `type` matching a template name trigger
template expansion:

```yaml
---
type: my-template
name: fedora-42-build
parents:
  - fedora-42-base
  - fedora-42-updates
```

This expands into the final koji objects through recursive template processing.


## Types

koji-habitude supports all core Koji object types with fully implemented
Pydantic models:

### Core Types

- **`tag`**: Build tags with inheritance chains and external repositories
- **`external-repo`**: External package repositories with URL validation
- **`user`**: Koji users and permissions with group membership
- **`target`**: Build targets linking build and destination tags
- **`host`**: Build hosts and their configurations with architecture support
- **`group`**: Package groups and their memberships
- **`channel`**: Build channels with host assignments
- **`permission`**: User permission definitions

### Dependencies

The system automatically detects dependencies between objects using the
implemented `dependency_keys()` methods:

- **Tags** depend on parent tags and external repositories
- **Targets** depend on build and destination tags
- **Groups** depend on users and permissions
- **Users** depend on groups and permissions
- **Hosts** depend on channels
- **Channels** depend on hosts
- **External repos** and **permissions** have no dependencies

### Dependency Resolution

The implemented Resolver and Solver modules provide intelligent dependency
resolution:

1. **Resolver Module**: Handles external dependencies and creates placeholders
   for missing objects
2. **Solver Module**: Creates tiered execution plans with priority-based
   ordering
3. **Automatic Splitting**: Cross-tier dependencies are resolved through object
   splitting
4. **Tiered Execution**: Objects are processed in dependency-resolved tiers to
   ensure proper ordering

The system handles complex dependency scenarios including circular references
and cross-tier dependencies through sophisticated graph algorithms.


## Requirements

- [Python](https://python.org) 3.8+
- [Koji](https://pagure.io/koji) client libraries
- [Click](https://click.palletsprojects.com/) for CLI
- [PyYAML](https://pyyaml.org/) for configuration parsing
- [Jinja2](https://jinja.palletsprojects.com/) for template processing


## Installation

```bash
pip install -e .
```


## Contact

**Author**: Christopher O'Brien <obriencj@gmail.com>

**Original Git Repo**: https://github.com/obriencj/koji-habitude


## AI Assistance Disclaimer

This project was developed with assistance from [Claude](https://claude.ai)
(Claude 3.5 Sonnet) via [Cursor IDE](https://cursor.com). The AI assistant
helped with bootstrapping, unit tests, and documentation while following the
project's functional programming principles and coding standards.

See [VIBE.md](VIBE.md) for a very human blurb about how much of an impact this
has had on various files.


## License

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <https://www.gnu.org/licenses/>.


<!-- The end -->
