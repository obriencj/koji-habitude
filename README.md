# koji-habitude

> **⚠️ Work In Progress**: This project is currently under development and is not yet functional.


## Overview

koji-habitude is a configuration management tool for [Koji](https://pagure.io/koji) build systems. It provides a declarative approach to managing koji objects through YAML templates and data files, with intelligent dependency resolution and tiered execution.

The tool synchronizes local koji data expectations with a hub instance, allowing you to:
- Define koji objects (tags, external repos, users, targets, hosts, groups) in YAML
- Use Jinja2 templates for dynamic configuration generation  
- Automatically resolve dependencies between objects (tag inheritance)
- Apply changes in the correct order through tiered execution
- Validate configurations offline before deployment


## CLI

koji-habitude is built using [Clique](https://github.com/obriencj/python-clique) and provides three main commands:


### Synchronize with Koji Hub

```bash
koji-habitude sync [OPTIONS] DATA [DATA...]
```

**Options:**
- `DATA`: directories or files to work with
- `--templates PATH`: location to find templates that are not available in `DATA`
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

Shows all templates found in the given locations with their configuration details.


### Validate Configuration

```bash
koji-habitude validate [OPTIONS] DATA [DATA...]
```

Validates templates and data files without connecting to koji, checking for:
- Template syntax and structure
- Circular dependencies
- Missing dependencies
- Data consistency


## Templates

Templates use [Jinja2](https://jinja.palletsprojects.com/) for dynamic content generation. Each template is defined in YAML with the following structure:

```yaml
---
name: my-template
template: |
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
name: my-template
template_file: my-template.j2
schema:
  # Optional schema validation
```


### Template Expansion

When processing data files, objects with `type` matching a template name trigger template expansion:

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

koji-habitude supports all core Koji object types:

### Core Types

- **`tag`**: Build tags with inheritance chains and external repositories
- **`external-repo`**: External package repositories  
- **`user`**: Koji users and permissions
- **`target`**: Build targets linking build and destination tags
- **`host`**: Build hosts and their configurations
- **`group`**: Package groups and their memberships

### Dependencies

The system automatically detects dependencies between objects:

- Tags depend on parent tags and external repositories
- Targets depend on build and destination tags
- Groups depend on tags and users
- Hosts depend on users

### Dependency Resolution

Objects are processed in dependency-resolved tiers:
1. **Tier 1**: Objects with no dependencies (external-repos, users)
2. **Tier 2**: Objects depending only on Tier 1 (basic tags, hosts)
3. **Tier N**: Objects with increasingly complex dependency chains

Cross-dependencies within the same tier are resolved through automatic deferral mechanisms.


## Requirements

- [Python](https://python.org) 3.8+
- [Koji](https://pagure.io/koji) client libraries
- [Clique](https://github.com/obriencj/python-clique) for CLI
- PyYAML for configuration parsing
- Jinja2 for template processing

## Installation

```bash
pip install -e .
```


## Contact

**Author**: Christopher O'Brien <obriencj@gmail.com>

**Original Git Repo**: *Coming soon*


## AI Assistance Disclaimer

This project was developed with assistance from [Claude](https://claude.ai) (Claude 3.5 Sonnet) via Cursor IDE. The AI assistant helped with bootstrapping and documentation while following the project's functional programming principles and coding standards.

## License

This project is licensed under the GNU General Public License v3.0.

```
koji-habitude - Synchronize local koji data expectations with hub instance
Copyright (C) 2025 Christopher O'Brien

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
