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
from typing import Any, ClassVar, Dict, Iterator, Optional, Set

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jinja2 import Template as Jinja2Template
from jinja2.exceptions import TemplateError as Jinja2TemplateError
from jinja2.exceptions import TemplateSyntaxError as Jinja2TemplateSyntaxError
from jinja2.exceptions import UndefinedError
from jinja2.meta import find_undeclared_variables

from .exceptions import (TemplateError, TemplateOutputError,
                         TemplateRenderError, TemplateSyntaxError)
from .models import BaseObject, Field, field_validator


logger = logging.getLogger("koji_habitude.templates")


class TemplateCall(BaseObject):

    """
    Represents a YAML doc that needs to be expanded into zero or more
    new docs via a Template.
    """

    # this value is overridden in instances
    typename: ClassVar[str] = "template-call"
    name: Optional[str] = Field(alias='name', default=None)


    @property
    def template_name(self) -> str:
        return self.yaml_type


    @field_validator('name', mode='before')
    def validate_name(cls, value: str):
        pass


class Template(BaseObject):
    """
    A Template allows for the expansion of some YAML data into zero or
    more YAML docs, via Jinja2
    """

    typename: ClassVar[str] = "template"

    defaults: Dict[str, Any] = Field(alias='defaults', default_factory=dict)
    template_file: Optional[str] = Field(alias='file', default=None)
    template_content: Optional[str] = Field(alias='content', default=None)
    template_schema: Optional[Dict[str, Any]] = Field(alias='schema',
                                                      default=None)
    description: Optional[str] = Field(alias='description', default=None)

    _undeclared: Set[str] = None
    _jinja2_template: Jinja2Template = None
    _base_path: Optional[Path] = None


    @property
    def base_path(self) -> Optional[Path]:
        """
        The base path for the template file, used for resolving
        relative paths
        """

        return self._base_path


    @property
    def jinja2_template(self) -> Jinja2Template:
        """
        Access the Jinja2 template object
        """

        return self._jinja2_template


    @property
    def undeclared(self):
        """
        The list of variable names which are referenced in the Jinja2
        template, but which are not defined in the defaults
        """

        return self._undeclared


    def model_post_init(self, __context: Any):
        super().model_post_init(__context)

        if self.template_content:
            if self.template_file:
                raise TemplateError(
                    original_error=ValueError(
                        "Template content is not allowed when template file is specified"
                    ),
                    template=self,
                )

            jinja_env = Environment(
                trim_blocks=True,
                lstrip_blocks=True,
                undefined=StrictUndefined)

            try:
                ast = jinja_env.parse(self.template_content)
            except Jinja2TemplateSyntaxError as e:
                raise TemplateSyntaxError(
                    original_error=e,
                    template=self,
                ) from e
            except Jinja2TemplateError as e:
                raise TemplateError(
                    original_error=e,
                    template=self,
                ) from e

        else:
            if not self.template_file:
                raise TemplateError(
                    original_error=ValueError(
                        "Template content is required when template file is not specified"
                    ),
                    template=self,
                )

            elif Path(self.template_file).is_absolute():
                raise TemplateError(
                    original_error=ValueError(
                        "Absolute paths are not allowed with template file loading"
                    ),
                    template=self,
                )

            if self.filename:
                base_path = Path(self.filename).parent
            else:
                base_path = Path.cwd()
            self._base_path = base_path

            loader = FileSystemLoader(base_path)
            jinja_env = Environment(
                loader=loader,
                trim_blocks=True,
                lstrip_blocks=True,
                undefined=StrictUndefined)

            try:
                src = loader.get_source(jinja_env, self.template_file)[0]
                ast = jinja_env.parse(src)
            except Jinja2TemplateSyntaxError as e:
                raise TemplateSyntaxError(
                    original_error=e,
                    template=self,
                    template_file=self.template_file,
                ) from e
            except Jinja2TemplateError as e:
                raise TemplateError(
                    original_error=e,
                    template=self,
                    template_file=self.template_file,
                ) from e

        self._undeclared = find_undeclared_variables(ast)
        self._jinja2_template = jinja_env.from_string(ast)


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
        """
        Return the set of variable names which are referenced in the Jinja2
        template, but which are not defined in the defaults
        """

        return self._undeclared.difference(self.defaults)


    def render(self, data: Dict[str, Any]) -> str:
        """
        Render the template with the given data into a str
        """

        if not self.validate_call(data):
            raise TemplateRenderError(
                original_error=ValueError(f"Data validation failed for template {self.name!r}"),
                template=self,
                data=data,
            )

        merged_data = dict(self.defaults, **data)
        try:
            return self._jinja2_template.render(**merged_data)
        except UndefinedError as e:
            raise TemplateRenderError(
                original_error=e,
                template=self,
                data=data,
            ) from e


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

        rendered = self.render(data)

        try:
            for obj in yaml.safe_load_all(rendered):
                if not isinstance(obj, dict):
                    raise TemplateOutputError(
                        message="Template returned non-dict object",
                        template=self,
                        data=data,
                        rendered_content=rendered,
                    )
                obj.update(merge)
                yield obj
        except yaml.YAMLError as e:
            raise TemplateOutputError(
                message=f"Template rendered invalid YAML: {e}",
                template=self,
                data=data,
                rendered_content=rendered,
                original_exception=e,
            ) from e


    def render_call(self, call: TemplateCall):
        return self.render_and_load(call.data)


# The end.
