# koji-habitude

** WORK IN PROGRESS **
This project is not production ready. It's coming along fast, but there are challenges
cropping up all of the time. Until this project has a version of 1.0, do not attempt
to use it with a production Koji instance.


## Current Status

**✅ Completed:**
- CLI framework with all core commands (`sync`, `diff`, `expand`, `list-templates`)
- Comprehensive data models for all Koji object types (8 CORE_MODELS)
- Pydantic validation with field constraints and proper error handling
- Dependency resolution architecture (Resolver and Solver modules)
- Tiered execution system with automatic splitting for cross-dependencies
- Comprehensive unit test coverage (349 tests across 17 test files)
- Template expansion and YAML processing
- Processor module with state machine for synchronization
- Change tracking and reporting system
- Multicall integration for efficient Koji operations
- **Sync and diff commands with full koji integration**
- **Complete processor implementation with DiffOnlyProcessor for dry-run operations**

**🚧 In Progress:**
- CLI testing coverage improvements
- Performance optimization and error handling improvements

**📋 Next Steps:**
- Enhance CLI testing coverage
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

**✅ Fully Implemented:**
- `list-templates` - List and inspect available templates
- `expand` - Expand templates and output final YAML
- `sync` - Synchronize with Koji hub (full implementation with koji integration)
- `diff` - Show differences using DiffOnlyProcessor (full implementation)


### Synchronize with Koji Hub

```bash
koji-habitude sync [OPTIONS] DATA [DATA...]
```

**✅ Fully Implemented**: Synchronizes local koji data expectations with hub instance using the Processor module.

**Options:**
- `DATA`: directories or files to work with
- `--templates PATH`: location to find templates that are not available in `DATA`
- `--profile PROFILE`: Koji profile to use for connection (default: 'koji')
- `--show-unchanged`: Show objects that don't need any changes

**Features:**
- Loads templates and data files with dependency resolution
- Processes objects in dependency-resolved order using Solver
- Fetches current state from koji using multicall optimization
- Compares local expectations with current koji state
- Applies changes in correct order with error handling
- Provides detailed change reporting and progress updates

```bash
koji-habitude diff [OPTIONS] DATA [DATA...]
```

**✅ Fully Implemented**: Shows what changes would be made without applying them using DiffOnlyProcessor.

**Options:**
- `DATA`: directories or files to work with
- `--templates PATH`: location to find templates that are not available in `DATA`
- `--profile PROFILE`: Koji profile to use for connection (default: 'koji')
- `--show-unchanged`: Show objects that don't need any changes

**Features:**
- Same processing as sync command but skips write operations
- Uses DiffOnlyProcessor to prevent actual changes
- Provides detailed change analysis and dependency reporting

### List Available Templates

```bash
koji-habitude list-templates [OPTIONS] PATH [PATH...]
```

**✅ Fully Implemented**: Shows all templates found in the given locations with their configuration
details.

**Options:**
- `PATH`: directories containing template files
- `--templates PATH`: load only templates from the given paths
- `--yaml`: show expanded templates as YAML
- `--full`: show full template details including file locations and trace information
- `--select NAME`: select specific templates by name


### Validate Configuration

```bash
koji-habitude expand --validate [OPTIONS] DATA [DATA...]
```

**✅ Available**: Validation is currently available as a flag in the `expand` command.

**Features:**
- Validates templates and data files without connecting to koji
- Checks template syntax and structure
- Validates YAML structure and Pydantic model constraints
- Processes through full template expansion pipeline
- Returns validation errors for malformed data


### Expand Templates and Data

```bash
koji-habitude expand [OPTIONS] DATA [DATA...]
```

**✅ Fully Implemented**: Expands templates and data files into final YAML output.

**Options:**
- `DATA`: directories or files to work with
- `--templates PATH`: location to find templates that are not available in
  `DATA`

This command loads templates from the specified locations, processes the data files through
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


## Architecture

koji-habitude implements a sophisticated architecture for managing koji object synchronization:

### Core Components

- **Template System**: Jinja2-based template expansion with recursive processing
- **Dependency Resolution**: Resolver and Solver modules for intelligent ordering
- **Processor Module**: State machine-driven synchronization engine
- **Change Tracking**: Comprehensive reporting of modifications and differences

### Processor Module

The `Processor` class is the core synchronization engine that manages the read/compare/apply cycle:

- **State Machine**: `ProcessorState` enum manages processing phases (READY_CHUNK → READY_READ → READY_COMPARE → READY_APPLY)
- **Chunking**: Processes objects in configurable chunks for memory efficiency
- **Multicall Integration**: Uses koji's multicall API for efficient batch operations
- **Change Tracking**: `ChangeReport` system tracks all modifications with detailed change explanations
- **Dry-Run Support**: `DiffOnlyProcessor` for previewing changes without applying them
- **Error Handling**: Comprehensive error handling with state management and recovery
- **Progress Reporting**: Step-by-step progress reporting with callback support

### Data Flow

1. **Loading**: YAML files loaded via `MultiLoader` and `YAMLLoader`
2. **Expansion**: Templates expanded recursively through `ExpanderNamespace`
3. **Resolution**: Dependencies resolved via `Resolver` and `Solver`
4. **Processing**: Objects processed in dependency order via `Processor`
5. **Synchronization**: Changes applied to koji hub with multicall optimization


## Requirements

- [Python](https://python.org) 3.8+
- [Koji](https://pagure.io/koji) client libraries
- [Click](https://click.palletsprojects.com/) for CLI
- [PyYAML](https://pyyaml.org/) for configuration parsing
- [Jinja2](https://jinja.palletsprojects.com/) for template processing
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation


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
