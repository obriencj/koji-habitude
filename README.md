# koji-habitude

koji-habitude is an object management tool for [Koji](https://pagure.io/koji)
build systems. It provides a declarative approach to managing koji objects
through YAML templates and data files.

This project is an offshoot of [koji-box](https://github.com/obriencj/koji-box),
fulfilling the need for populating a boxed koji instance with a bunch of tags
and targets. However it is being written such that it can be used with any koji
deployment, in the hopes that it may bring joy into the lives of those trying to
keep project packagers happy.

**Key Features:**

- Define koji objects (tags, external repos, users, targets, hosts, groups,
  channels, permissions, build types, archive types) in YAML
- Use Jinja2 templates for dynamic configuration generation
- Automatically resolve dependencies between objects (tag inheritance)
- Apply changes in the correct order through tiered execution
- Validate configurations offline before deployment


## Command-Line Interface

koji-habitude provides a comprehensive CLI built with
[Click](https://click.palletsprojects.com/) for managing Koji objects. The CLI
includes:

- **Primary commands**: `apply`, `compare`, `expand`, `fetch`, `dump`,
  `list-templates`, `diff`, and `edit`
- **Template subcommands**: Work with individual templates using `template
  show`, `template expand`, `template compare`, `template diff`, `template
  apply`

For detailed CLI documentation with all options, examples, and use cases, see
the [Command-Line Interface documentation](docs/cli/index.rst) in the full
documentation.


## YAML Format & Templates

YAML files can be single or multi-document, processed in-order. Each document
has a `type` key indicating the document type. Core types include `template`,
`tag`, `target`, `user`, `group`, `host`, `channel`, `permission`,
`content-generator`, `build-type`, `archive-type`, and `external-repo`.
Templates define new types based on their name.

Templates use [Jinja2](https://jinja.palletsprojects.com/) for dynamic content
generation, allowing you to create reusable patterns for koji objects. When
processing data files, objects with `type` matching a template name trigger
template expansion, creating final koji objects through recursive processing.

For complete YAML format documentation and detailed examples, see the
[YAML Format Specification](docs/yaml_format.rst) in the full documentation.


## Architecture

koji-habitude supports all core Koji object types with fully implemented
Pydantic models: tags, external repos, users, targets, hosts, groups,
channels, permissions, content generators, build types, and archive types.

The system automatically detects dependencies between objects (e.g., tag
inheritance) and provides intelligent resolution through tiered execution,
ensuring objects are processed in the correct order. The architecture includes:

- **Template System**: Jinja2-based template expansion with recursive processing
- **Dependency Resolution**: Automatic detection and tiered execution ordering
- **Remote Models**: Complete set of remote object models for fetching and comparing
- **State Synchronization**: State machine-driven processor with multicall integration
- **Change Tracking**: Detailed tracking of all modifications with explanations
- **Dry-Run Support**: Preview changes without applying them
- **Bidirectional**: Fetch remote state to YAML, or dump remote objects by pattern

**Data Flow**: YAML files → Template expansion → Dependency resolution → Tiered
processing → Koji hub


## Requirements & Installation

**Requirements:**

- Python 3.8+
- [Koji](https://pagure.io/koji)
- [Click](https://palletsprojects.com/p/click/)
- [PyYAML](https://pyyaml.org/)
- [Jinja2](https://palletsprojects.com/p/jinja/)
- [Pydantic](https://docs.pydantic.dev/)

**Installation:**

```bash
pip install -e .
```


## Contact & License

**Author**: Christopher O'Brien <obriencj@gmail.com>

**Original Git Repository**: https://github.com/obriencj/koji-habitude

**Documentation**: https://obriencj.github.io/koji-habitude

**AI Assistance**: This project was developed with assistance from
[Claude](https://claude.ai) (Claude 3.5 and 4.5 Sonnet) via [Cursor
IDE](https://cursor.com).

**License**: GNU General Public License v3 or later. See
<https://www.gnu.org/licenses/> for details.


<!-- The end -->
