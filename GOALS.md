
GOALS:

This project is feeds syncrhonizes local koji data expectations with a hub
instance.

It includes a CLI which can be invoked with a koji profile (optional), a
templates path, and a data directory.

## Loading Template Types

At launch any YAML files in the templates path are loaded, and become available
as templates by name based off of a value in their metadata. Templates specify
the path to a jinja2 template (or include it inline), and optionally specify the
schema for the object that they are invoked with.

## Loading Object Data

At launch any YAML files in the data directory are loaded. Each YAML file is
expected to contain 0 or more YAML objects. Each YAML object will have a `type:`
value that indicates whether it's one of the core koji types, or the name of a
defined template.

Each data type has a `name:` field, which when combined with the core type
creates a unique identifier pair `(type, name)`. For example a tag named
fedora-42-build-base may look like

```
---
type: tag
name: fedora-42-build-base
tag-extras:
  foo: bar
external-repos:
  - name: fedora-42-Updates
    priority: 100
  - name: fedora-42-Everything
    priority: 110
```

THe YAML is loaded via `YAMLLoader` (or through a `MultiLoader`) in loader.py

Each data object loaded from the stream has its type resolved from a model
registry (implemented in `Namespace`, namespace.py), which has the core models
(tag, external-repo, user, target, host, group) and the registered templates. If
the type maps to a core model, an instance is created from the data. If the type
maps to a template the template is expanded and inlined, which is explained in
the next section

Each of the objects, and those objects expanded from templates, are placed into
a shared Object Map, based on their `(type, name)` tuple.


## Template Inlining

Templates act as a sort of macro system, accepting data and converting it into
zero or more new data entries.

The process is as follows:
* the template is resolved by type name (Namespace does this during `expand()`)
* the data is passed to a schema to validate it, if one is configured for the
  template
* the data is passed as the environment for the underlying jinja2 template
* the output of the jinja2 template is parsed as a multi-entry YAML document
* each object of the output is parsed as before, potentially triggering further
  template expansion
* the invoking namespage inlines the fully expanded template objects into its
  object stream, all as instances of the core model types
* the namespace is full of objects


## Dependency Resolution

Each type in the model is aware that certain values in its configuration
reference a requirement that a value exist already in the system. For example
the inheritance of a tag structure, each entry references another tag, which
must already exist.

Each model type has a `dependent_keys()` method which will return a list of the
`(type, name)` keys that this object depends on.

To take the data from a fully fed and expanded Namespace and produce a stream of
objects in dependency-solved ordering we use a `Solver` from solver.py, and a a
`Resolver` from resolver.py

The Solver creates internal Node tree representing every item. It obtains these
items by referencing the Resolver, which in turn will either fetch the object
from the Namespace, or create a placeholder object indicating a reference that
doesn't exist in the main data set of the Namespace.

The Solver follows an internal algorithm to produce a stream of objects from its
Node tree.


## Model Application into Koji

The stream of objects from the model tree can then be fed into an applicator
(TBD) which chunks the stream into groups of a predetermined size, while
preserving the ordering.

The applicator will then sync the object states into a Koji instance using
optimizations such as multicalls to first look up the current state and then
send the changes that are necessary back.

It maintains a report on what changes have been made.

An applicator running in only "diff mode" might not actually commit the changes,
it might prefer to only collect the differences and then report them back.
