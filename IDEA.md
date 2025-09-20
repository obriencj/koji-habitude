

`model` has
  * core types
  * `Template` - for template definition
  * `TemplateCall` - for invocations of templates (ie. type not found)

`namespace.Namespace`
  * `.set_types(dict)` has a type registry, recording types by name
    None is a special type key that should map to what class to use for
    a missing type, generally a `TemplateCall`

  * `.to_object(dict_obj)` finds appropriate type in registry and
    instantiates it with dict_obj as the data

  * `.feed(model_obj)` accepts a model object into the namespace. At
    this point it is only appending to a list of objects. Any Template
    instances found get added via `.add_template()`, otherwise the
    object is appended to the `self.unexpanded` list list.

  * `.expand()`
    * iterates over `._expand(self.unexpanded)`
    * calls `self.add` on items

  * `._expand(seq)` takes the sequence and begins walking it in order
    * if a core type, yields it
    * if it's a TemplateCall, `yield from self._expand_template(obj)`

  * `._expand_template(obj)`
    * we resolve the Template, use it to expand the TemplateCall
    * use `load_object` on the expanded yaml objects
    * pre-walk the sequence, templates get added via `.add_template`
    * yield from `._expand(seq)` -- or maybe just copy the behavior here

`loader.YAMLLoader`
  * accepts a Namespace, filename
  * tracks line number for each object
  * embeds `'__from__': {'filename': filename, 'lineno': lineno}` in parsed
    objects
  * `.resolve_all()` converts all loaded dicts into model types, via
    `Namespace.load_object`
  * `.iter()` yields resolved objects
  * .`inject()` adds all objects into the namespace

`loader.PyLoader`
  * accepts a Namespace, filename
  * imports a python module
  * `.iter()` yields discovered types in module
  * .`inject()` adds all objects into the namespace

`loader.MultiLoader`
  * accepts a Namespace
  * `.add_ext(".yaml", YAMLLoader)`
  * `.get_loader(path)` -> instance of loader for extension
  * `.inject(filename)` creates the relevant loader for the file, runs
    its inject method, discards it
  * `.inject_all(paths)` uses flatten_paths with its configured
    extensions to identify all files from paths, create their loaders,
    and call inject on them.

`loader.find_files(path, extensions)`
  * walks a directory looking for files with extensions, returns
    them in predictable order

`loader.flatten_paths(paths, extensions, strict)`
  * accepts list mixing files and directories
  * flattens and de-duplicates the resulting file paths
  * returns a list of files matching extensions
  * note: if given foo_bar.bin as a direct argument, but .bin is not
    a valid extension, it will not be in the results, even though it is
    explicitly added in the paths. set strict to False to include them
    anyway


CLI Loading stage
  * creates a primary Namespace with valid types

  * if `--templates` is specified
    * create a template Namespace with just the "template" type configured
    * create `loader.MultiLoader(template_ns)` with valid extensions
    * run `multiloader.inject_all(args.templates)`
    * `primary_ns.update(template_ns)`

  * create `loader.MultiLoader(primary_ns)` with valid extensions
  * `multiloader.inject_all(paths_from_args)`

  we now have a single primary Namespace, filled with objects marshalled
  from files, with any template specific ones pre-loaded.

CLI Template exmapsion stage

  * for each of the
