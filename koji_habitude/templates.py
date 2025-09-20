"""
koji_habitude.template

Template loading and Jinja2 expansion system for koji object templates.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated, Mostly Human


import logging
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Generator

from jinja2 import Environment, FileSystemLoader, Template as Jinja2Template
import yaml


logger = logging.getLogger("koji_habitude.templates")


class TemplateCall:

    """
    Represents a YAML doc that needs to be expanded into zero or more
    new docs via a Template.
    """

    def __init__(self, data):
        self.typename = data['type']
        self.data = data


class Template:

    """
    A Template allows for the expansion of some YAML data into zero or
    more YAML docs, via Jinja2
    """

    typename = "template"


    def __init__(
        self,
        name: str,
        template_data: Dict[str, Any],
        base_path: Optional[Path] = None):

        """
        Initialize template.

        Args:
            name: Name of the template
            template_data: Template configuration data
            base_path: Base path for this definition, for loading jinja2
                       from file
        """

        name = name and name.strip()
        if not name:
            raise TemplateValueError("Template name is required")

        self.name = name
        self.data = template_data

        template_content = template_data.get('template')
        template_file = template_data.get('template_file')

        if template_file:
            if not base_path:
                # TODO: should this just become Path.cwd()?
                raise TemplateValueError("Base path is required when template file is specified")

            base_path = Path(base_path)
            if not base_path.exists():
                raise FileNotFoundError(f"Base path not found: {base_path}")

            if not base_path.is_dir():
                raise NotADirectoryError(f"Base path is not a directory: {base_path}")

            if template_content:
                raise TemplateValueError("Template content is not allowed when template file is specified")

        elif not template_content:
            raise TemplateValueError("Template content is required when template file is not specified")

        # record these so we can tell if we got it from a file or inline later
        self.base_path = base_path
        self.template_file = template_file
        self.template_content = template_content

        # TODO: load the schema into a JSON schema validator if present
        self.schema = template_data.get('schema')

        if template_file:
            jinja_env = Environment(
                loader=FileSystemLoader(base_path),
                trim_blocks=True,
                lstrip_blocks=True
            )
            self.jinja2_template = jinja_env.get_template(template_file)
        else:
            jinja_env = Environment(
                trim_blocks=True,
                lstrip_blocks=True
            )
            self.jinja2_template = jinja_env.from_string(template_content)


    def __repr__(self) -> str:
        """
        Return a string representation of the template.
        """
        return f"Template(name={self.name}, template_file={self.template_file}, template_content={self.template_content})"


    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate data against template schema if configured.

        Args:
            data: Data to validate

        Returns:
            True if validation passes or no schema configured
        """

        if not self.schema:
            return True

        # TODO: Implement schema validation
        return True


    def render(self, data: Dict[str, Any]) -> str:
        """
        Render the template with the given data into a str
        """

        if not self.validate_data(data):
            msg = f"Data validation failed for template {self.name!r}")
            raise TemplateValueError(msg)

        return self.jinja2_template.render(**data)


    def render_and_load(
            self,
            data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:

        """
        Render the template with the given data and yield the resulting
        YAML documents
        """

        # We want some ability to trace provenance of expanded entries,
        # so we'll fill in a __trace__ value (indicating what Template
        # was used) and the __file__ and __line__ values from the original
        # data so we can find the TemplateCall

        traceval = {
            "template": self.name,
            "file": self.filename,
            "line": self.lineno,
        }

        trace = data.get("__trace__")
        if trace is None:
            trace = [traceval]
        else:
            trace.append(traceval)

        merge = {"__trace__": trace}

        filename = data.get("__file__")
        if filename:
            merge["__file__"] = filename
        lineno = data.get("__line__")
        if lineno:
            merge["__line__"] = lineno

        for obj in yaml.safe_load_all(self.render(data)):
            obj.update(merge)
            yield obj


    def render_call(self, call: TemplateCall):
        return self.render_and_load(call.data)


class TemplateValueError(ValueError):
    """
    Exception raised for template validation errors.
    """

    pass


def _iter_load_templates_from_file(
    yaml_file: Path,
    strict: bool = True) -> Iterator[Template]:

    """
    Iterate over templates in a YAML file.
    """

    print("iter_load_templates_from_file", yaml_file, strict)

    # TODO: it would be great if we could identify the line number of
    # templates as we load them, this would really aid in debugging
    # and even plain introspection.

    if strict:
        # if an exception happens, we let that sucker propagate.
        with open(yaml_file, 'r') as f:
            for doc in yaml.safe_load_all(f):
                print("doc", doc)
                if doc and doc.get('type') == 'template':
                    yield Template(doc.get('name'), doc, yaml_file.parent)
        return

    # if an exception happens, we log it and continue.
    try:
        with open(yaml_file, 'r') as f:
            try:
                loaded_docs = yaml.safe_load_all(f)
            except yaml.YAMLError as e:
                logger.error(f"Error loading template file {yaml_file}: {e}")
                return

            for doc in loaded_docs:
                if doc and doc.get('type') == 'template':
                    try:
                        yield Template(doc.get('name'), doc, yaml_file.parent)
                    except Exception as e:
                        logger.error(f"Error processing template file {yaml_file}: {e}")

    except Exception as e:
        logger.error(f"Error loading template file {yaml_file}: {e}")
        return


def _iter_load_templates(
    template_path: Path,
    strict: bool = True) -> Iterator[Template]:

    """
    Iterate over templates in a directory.
    """

    if not template_path.exists():
        raise FileNotFoundError(f"Templates path not found: {template_path}")

    if template_path.is_file():
        return _iter_load_templates_from_file(template_path, strict=strict)

    yaml_files = list(template_path.glob("*.yaml")) + list(template_path.glob("*.yml"))

    # Load all YAML files in the templates directory
    for yaml_file in yaml_files:
        yield from _iter_load_templates_from_file(yaml_file, strict=strict)


def load_templates(
    template_path: str|Path,
    allow_redefinition: bool = False,
    strict: bool = True) -> Dict[str, Template]:

    """
    Load all YAML templates from directory. Skips all non-template declarations.

    Args:
        templates_path: Path to directory containing template files
        strict: Whether to raise an error if a template is not found or is invalid. If False, will log an error and continue.

    Returns:
        Dictionary mapping template names to Template objects
    """

    registry = TemplateRegistry(allow_redefinition=allow_redefinition, strict=strict)
    registry.load_templates(Path(template_path))
    return registry.templates


# The end.
