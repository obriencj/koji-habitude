"""
koji_habitude.template

Template loading and Jinja2 expansion system for koji object templates.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


import logging

from pydantic import Field, PrivateAttr
from pathlib import Path
from typing import Any, ClassVar, Dict, Iterator, Optional, Set

from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template as Jinja2Template
from jinja2.exceptions import UndefinedError, TemplateNotFound
from jinja2.meta import find_undeclared_variables
import yaml

from .models import BaseObject


logger = logging.getLogger("koji_habitude.templates")


class TemplateCall:

    """
    Represents a YAML doc that needs to be expanded into zero or more
    new docs via a Template.
    """

    def __init__(self, data: Dict[str, Any]):
        self.typename: str = data['type']
        self.data: Dict[str, Any] = data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateCall':
        return cls(data)


class Template(BaseObject):
    """
    A Template allows for the expansion of some YAML data into zero or
    more YAML docs, via Jinja2
    """

    typename: ClassVar[str] = "template"

    defaults: Dict[str, Any] = Field(alias='defaults', default_factory=dict)
    template_file: Optional[str] = Field(alias='file', default=None)
    template_content: Optional[str] = Field(alias='content', default=None)
    template_schema: Optional[Dict[str, Any]] = Field(alias='schema', default=None)

    _undeclared: Set[str]
    _jinja2_template: Jinja2Template
    _base_path: Path | None = None


    @property
    def base_path(self) -> Optional[Path]:
        """Access the base path."""
        return self._base_path

    @property
    def jinja2_template(self) -> Jinja2Template:
        """Access the Jinja2 template object."""
        return self._jinja2_template


    def model_post_init(self, __context: Any):
        super().model_post_init(__context)

        if self.template_content:
            if self.template_file:
                raise TemplateException(
                    "Template content is not allowed when template file is specified",
                    self.filename, self.lineno)

            jinja_env = Environment(
                trim_blocks=True,
                lstrip_blocks=True,
                undefined=StrictUndefined)
            ast = jinja_env.parse(self.template_content)

        else:
            if not self.template_file:
                raise TemplateException(
                    "Template content is required when template file is not specified",
                    self.filename, self.lineno)

            elif Path(self.template_file).is_absolute():
                raise TemplateException(
                    "Absolute paths are not allowed with template file loading",
                    self.filename, self.lineno)

            base_path = Path(self.filename).parent if self.filename else Path.cwd()
            self._base_path = base_path

            loader = FileSystemLoader(base_path)
            jinja_env = Environment(
                loader=loader,
                trim_blocks=True,
                lstrip_blocks=True,
                undefined=StrictUndefined)
            src = loader.get_source(jinja_env, self.template_file)[0]
            ast = jinja_env.parse(src)

        self._undeclared = find_undeclared_variables(ast)
        self._jinja2_template = jinja_env.from_string(ast)


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
        if self.template_schema:
            data['schema'] = self.template_schema

        return data


    def validate_call(self, data: Dict[str, Any]) -> bool:
        """
        Validate call data against template schema if configured.

        Args:
            data: Data to validate

        Returns:
            True if validation passes or no schema configured
        """

        if not self.template_schema:
            return True

        # TODO: Implement schema validation
        return True


    def get_missing(self):
        return self._undeclared.difference(self.defaults)


    def render(self, data: Dict[str, Any]) -> str:
        """
        Render the template with the given data into a str
        """

        if not self.validate_call(data):
            msg = f"Data validation failed for template {self.name!r}"
            raise TemplateValueError(msg)


        try:
            return self._jinja2_template.render(**dict(self.defaults, **data))
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


    @property
    def undeclared(self):
        return self._undeclared


    def render_call(self, call: TemplateCall):
        return self.render_and_load(call.data)


class TemplateException(Exception):
    """
    Exception raised for template errors.
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


class TemplateValueError(ValueError, TemplateException):
    """
    Exception raised for template validation errors.
    """
    pass


# The end.
