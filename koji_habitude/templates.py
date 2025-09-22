"""
koji_habitude.template

Template loading and Jinja2 expansion system for koji object templates.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


import logging
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Generator

from jinja2 import Environment, FileSystemLoader, Undefined, StrictUndefined
from jinja2.exceptions import UndefinedError
from jinja2.meta import find_undeclared_variables
import yaml

from .models import Base, BaseObject


logger = logging.getLogger("koji_habitude.templates")


class TemplateCall:

    """
    Represents a YAML doc that needs to be expanded into zero or more
    new docs via a Template.
    """

    def __init__(self, data):
        self.typename = data['type']
        self.data = data


class TemplateProtocol(Base):

    def validate(self, data: Dict[str, Any]) -> bool:
        ...
    def render(self, data: Dict[str, Any]) -> str:
        ...
    def render_and_load(self, data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        ...
    def render_call(self, call: TemplateCall) -> Iterator[Dict[str, Any]]:
        ...


class Template(BaseObject, TemplateProtocol):

    """
    A Template allows for the expansion of some YAML data into zero or
    more YAML docs, via Jinja2
    """

    typename = "template"


    def __init__(
        self,
        data: Dict[str, Any]):

        """
        Initialize template.

        Args:
            name: Name of the template
            template_data: Template configuration data
        """

        super().__init__(data)

        self.defaults = data.get('defaults', {})

        template_content = data.get('content')
        template_file = data.get('file')

        if self.filename:
            base_path = Path(self.filename).parent
        else:
            base_path = None

        if template_file:
            if not base_path:
                # TODO: should this just become Path.cwd()?
                raise TemplateValueError(
                    "Base path is required when template file is specified",
                    self.filename, self.lineno)

            base_path = Path(base_path)
            if not base_path.exists():
                raise FileNotFoundError(f"Base path not found: {base_path}")

            if not base_path.is_dir():
                raise NotADirectoryError(f"Base path is not a directory: {base_path}")

            if template_content:
                raise TemplateValueError(
                    "Template content is not allowed when template file is specified",
                    self.filename, self.lineno)

        elif not template_content:
            raise TemplateValueError(
                "Template content is required when template file is not specified",
                self.filename, self.lineno)

        # record these so we can tell if we got it from a file or inline later
        self.base_path = base_path
        self.template_file = template_file
        self.template_content = template_content

        # TODO: load the schema into a JSON schema validator if present
        self.schema = data.get('schema')

        # do not catch errors from the jinja2 environment, let them bubble up.
        # If there's a problem, we want to know about it.

        if template_file:
            loader = FileSystemLoader(base_path)
            jinja_env = Environment(
                loader=loader,
                trim_blocks=True,
                lstrip_blocks=True,
                undefined=StrictUndefined)
            src = loader.get_source(jinja_env, template_file)[0]
            ast = jinja_env.parse(src)
            self.undeclared = find_undeclared_variables(ast)
            self.jinja2_template = jinja_env.from_string(ast)
        else:
            jinja_env = Environment(
                trim_blocks=True,
                lstrip_blocks=True,
                undefined=StrictUndefined)
            ast = jinja_env.parse(template_content)
            self.undeclared = find_undeclared_variables(ast)
            self.jinja2_template = jinja_env.from_string(ast)


    def __repr__(self) -> str:
        """
        Return a string representation of the template.
        """

        return f"<Template(name={self.name})>"


    def to_dict(self):
        data = {
            'name': self.name,
        }
        if self.filename:
            data['__file__'] = self.filename
        if self.lineno:
            data['__line__'] = self.lineno
        if self.trace:
            data['__trace__'] = self.trace
        if self.defaults:
            data['defaults'] = self.defaults
        if self.template_file:
            data['file'] = self.template_file
        if self.template_content:
            data['content'] = self.template_content
        if self.schema:
            data['schema'] = self.schema

        return data


    def validate(self, data: Dict[str, Any]) -> bool:
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


    def get_missing(self):
        return self.undeclared.difference(self.defaults)


    def render(self, data: Dict[str, Any]) -> str:
        """
        Render the template with the given data into a str
        """

        if not self.validate(data):
            msg = f"Data validation failed for template {self.name!r}"
            raise TemplateValueError(msg)


        try:
            return self.jinja2_template.render(**dict(self.defaults, **data))
        except UndefinedError as e:
            msg = f"Undefined variable in template {self.name!r}: {e}"
            raise TemplateValueError(msg)


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
            "name": self.name,
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
            if not isinstance(obj, dict):
                raise TemplateValueError(
                    f"Template {self.name!r} returned non-dict object",
                    self.filename, self.lineno)
            obj.update(merge)
            yield obj


    def render_call(self, call: TemplateCall):
        return self.render_and_load(call.data)


class TemplateValueError(ValueError):
    """
    Exception raised for template validation errors.
    """

    def __init__(self, message, filename=None, lineno=None):
        if filename:
            if lineno:
                message = f"{message} at {filename}:{lineno}"
            else:
                message = f"{message} at {filename}"

        super().__init__(message)
        self.filename = filename
        self.lineno = lineno


# The end.
