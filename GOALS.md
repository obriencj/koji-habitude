
GOALS:

This project is feeds syncrhonizes local koji data expectations with a hub instance.

It includes a CLI which can be invoked with a koji profile (optional), a templates path, and a data directory.

## Loading Template Types

At launch any YAML files in the templates path are loaded, and become available as templates by name based off of a value in their metadata. Templates specify the path to a jinja2 template (or include it inline), and optionally specify the schema for the object that they are invoked with.

## Loading Object Data

At launch any YAML files in the data directory are loaded. Each YAML file is expected to contain 0 or more YAML objects. Each YAML object will have a `type:` value that indicates whether it's one of the core koji types, or the name of a defined template.

Each data type has a `name:` field, which when combined with the core type creates a unique identifier pair `(type, name)`. For example a tag named fedora-42-build-base may look like

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

Each data object loaded from the stream has its type resolved from a model registry, which has the core models (tag, external-repo, user, target, host, group) and the registered templates. If the type maps to a core model, an instance is created from the data. If the type maps to a template the template is expanded and inlined, which is explained in the next section

Each of the objects, and those objects expanded from templates, are placed into a shared Object Map, based on their `(type, name)` tuple.


## Template Inlining

Templates act as a sort of macro system, accepting data and converting it into zero or more new data entries.

The process is as follows:
* the template is resolved by type name
* the data is passed to a schema to validate it, if one is configured for the template
* the data is passed as the environment for the underlying jinja2 template
* the output of the jinja2 template is parsed as a multi-entry YAML document
* each object of the output is parsed as before, potentially triggering further template expansion
* eventually the flattened list of objects is yielded
* the invoking loader inlines the fully expanded template objects into its object stream, all as instances of the core model types
* the loader process will take those core types and inject them into the Object Map


## Dependency Resolution

Each type in the model is aware that certain values in its configuration reference a requirement that a value exist already in the system. For example the inheritance of a tag structure, each entry references another tag, which must already exist.

Each model type has a `dependent_keys()` and `dependents(obj_map)` method. The former will return a list of the `(type, name)` keys that this object depends on. The latter will dereference the objects from the object map.

The object map has one of two resolvers in it. When the object map is missing an dependency object, it will attempt to check with the resolver. The online resolver checks in the koji instance just to verify the entry already exists. If it doesn't, the object map may consider this a failure. In offline mode, the resolver simply records that the object is desired but not immediately available. This may be used to produce a warning.

To create a dependency tree, the object map will iterate over every object in its mapping. If an object has dependents, an inverse mapping will be created on the dependents, adding the child object's key via a `register_dependent(obj)` method. After every object has been reviewed, a second pass will happen, finding objects with empty dependent lists. These are "leaf" nodes, and they serve as the starting point for operations. The method `resolve_leaves()` produces an Object Tier containing al the objects found to have no dependents using the above method.

An Object Tier can be iterated over to get the individual objects at that tier. There is also a `next_tier()` method, which resolves all of the dependants as previously recorded, and creates a new Object Tier containing.

There may be special cases where an Object Tier has dependencies between two objects of the same tier (though very rare). This is resolved by a special method on the object `defer_deps(deplist)` which will return a new copy of the object that doesn't have the selected dependencies in its configuration, but introduces a new child dependency of type "deferred_$type" with the same name. This child is a wrapper for the original data. In this way some of the configuration is done at one tier, and then the rest deferred at a later tier

So eg. a if `('tag', 'a_1')` and `('tag', 'a_2')` depend on one another, then the object tier will create new `('tag', 'a_1')` that drops all of its problematic depdencencies, and has an injected dependency on a new `('deferred_tag', 'a_1')` that has the full data set It will also create a new `('tag', 'a_2')` with a  `('deferred_tag', 'a_2')` counterpart, to do the same. In this way the data can be CREATED at the current tier, and references to the cross-dependencies can be ADDED in the next tier.


## Model Application into Koji

When the first Object Tier is received, its internal cross-dependencies resolved via dep deferral, it can be iterated over. The Koji instance can be queried (via a multicall) to fetch the current state of chunks of data. The objects are fed their koji instance data, and are asked if they have update calls. If they do, those calls are made into a new multicall method to koji. These chunks of queries and updates can happen in parallel, as there should be zero cross-dependency links at this point.

Once all updates have been made, the Object Tier is replaced with its `next_tier()` and the process repeats until there result is None (due to there being no further dependents)


