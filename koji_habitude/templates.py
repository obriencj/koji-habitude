"""
koji_habitude.template

Template loading and Jinja2 expansion system for koji object templates.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


import logging
from enum import Enum
from pathlib import Path
from re import Pattern, compile
from typing import (
    Any, Callable, ClassVar, Dict, Iterator, List, Optional,
    Set, Tuple, Type, Union,
)

import yaml
from jinja2 import (
    Environment, FileSystemLoader, StrictUndefined,
    Template as Jinja2Template,
)
from jinja2.exceptions import (
    TemplateError as Jinja2TemplateError,
    TemplateSyntaxError as Jinja2TemplateSyntaxError,
    UndefinedError,
)
from jinja2.meta import find_undeclared_variables
from pydantic import create_model
from pydantic.fields import FieldInfo

from .exceptions import (
    TemplateError, TemplateOutputError,
    TemplateRenderError, TemplateSyntaxError,
)
from .models import (
    BaseModel, DataMixin, Field, IdentifiableMixin,
    LocalMixin, PrivateAttr, SubModel, field_validator,
)


logger = logging.getLogger(__name__)


class TemplateCall(DataMixin, BaseModel):
    """
    Represents a YAML doc that needs to be expanded into zero or more
    new docs via a Template.
    """

    typename: ClassVar[str] = "template"

    yaml_type: str = Field(alias='type')

    _data: Optional[Dict[str, Any]] = None


    @property
    def template_name(self) -> str:
        # For template calls, the template name is stored in the typename
        return self.yaml_type


def _array_type_helper(f: 'TemplateFieldDefinition') -> Type:
    if f.array_item_type:
        return List[f.array_item_type._python_type]  # type: ignore
    else:
        return List[Any]


def _enum_type_helper(f: 'TemplateFieldDefinition') -> Type:
    if f.validation and f.validation.enum_values:
        return Enum(
            f"Enum_{id(f)}",
            {str(v): v for v in f.validation.enum_values})  # type: ignore
    else:
        return str


def _object_type_helper(f: 'TemplateFieldDefinition') -> Type:
    if f.object_fields:
        inner = TemplateModelDefinition(
            name=f.object_type_name or f"Object_{id(f)}",
            fields=f.object_fields)
        return inner.get_model_class()
    else:
        return Dict[str, Any]


TYPE_REGISTRY: Dict[str, Union[Type, Callable]] = {
    'string': str,
    'str': str,
    'integer': int,
    'int': int,
    'float': float,
    'boolean': bool,
    'bool': bool,

    'dict': Dict[str, Any],

    'list': _array_type_helper,
    'array': _array_type_helper,
    'enum': _enum_type_helper,

    'object': _object_type_helper,

    # 'Tag': Tag,
    # 'User': User,
    # 'Group': Group,
    # 'Target': Target,
    # 'Host': Host,
    # 'Channel': Channel,
    # 'Permission': Permission,
    # 'ExternalRepo': ExternalRepo,
    # 'ContentGenerator': ContentGenerator,
    # 'ArchiveType': ArchiveType,
    # 'BuildType': BuildType,
}


class ValidationRule(SubModel):
    """
    Validation rules for a DynamicFieldDefinition
    """

    min_length: Optional[int] = Field(alias='min-length', default=None)
    max_length: Optional[int] = Field(alias='max-length', default=None)
    min_value: Optional[float] = Field(alias='min-value', default=None)
    max_value: Optional[float] = Field(alias='max-value', default=None)
    pattern: Optional[Pattern] = Field(alias='regex', default=None)
    enum_values: Optional[List[Any]] = Field(alias='enum', default=None)


    @field_validator('pattern', mode='before')
    def validate_pattern(cls, value: Any) -> Pattern:
        if isinstance(value, str):
            return compile(value)
        return value


    def as_field_validator(self, field_name: str) -> Callable:
        @field_validator(field_name, mode='before')
        def validate_field(cls, value: Any) -> Any:
            if self.min_length is not None:
                if len(value) < self.min_length:
                    raise ValueError(f"Field {field_name} must be at least {self.min_length} long")
            if self.max_length is not None:
                if len(value) > self.max_length:
                    raise ValueError(f"Field {field_name} must be at most {self.max_length} long")
            if self.min_value is not None:
                if value < self.min_value:
                    raise ValueError(f"Field {field_name} must be greater than or equal to {self.min_value}")
            if self.max_value is not None:
                if value > self.max_value:
                    raise ValueError(f"Field {field_name} must be less than or equal to {self.max_value}")
            if self.pattern is not None:
                if not self.pattern.match(value):
                    raise ValueError(f"Field {field_name} must match pattern {self.pattern}")
            if self.enum_values is not None:
                if value not in self.enum_values:
                    raise ValueError(f"Field {field_name} must be one of {self.enum_values}")
            return value

        return validate_field


class TemplateFieldDefinition(SubModel):
    """
    Defines a Field in a TemplateModel
    """

    type: str = Field(alias='type')
    alias: Optional[str] = None
    description: Optional[str] = None
    default: Optional[Any] = None
    required: bool = True
    validation: Optional[ValidationRule] = None
    array_item_type: Optional['TemplateFieldDefinition'] = None
    object_fields: Optional[Dict[str, 'TemplateFieldDefinition']] = None
    object_type_name: Optional[str] = None
    reference_type: Optional[str] = None

    _python_type: Optional[Type] = PrivateAttr(default=None)
    _field_info: Optional[FieldInfo] = PrivateAttr(default=None)


    @property
    def definition(self) -> Tuple[Type, FieldInfo]:
        return (self._python_type, self._field_info)


    def model_post_init(self, __context: Any):
        super().model_post_init(__context)

        # Convert type to Python type
        if self.type not in TYPE_REGISTRY:
            raise ValueError(f"Unknown dynamic model field type '{self.type}'")

        type_or_converter = TYPE_REGISTRY[self.type]
        if isinstance(type_or_converter, type):
            self._python_type = type_or_converter
        else:
            # these helper functions return something to be used as
            # the pydantic field type. They may need to use values
            # harvested from our configuration to do so
            # (eg. array_item_type, object_fields)
            self._python_type = type_or_converter(self)

        # Create field info
        kwargs: Dict[str, Any] = {}
        if self.alias:
            kwargs['alias'] = self.alias

        if self.description:
            kwargs['description'] = self.description

        if self.default is not None:
            kwargs['default'] = self.default

            # this will trigger validation (ie. type conversion) of
            # the default value to the correct type as defined by the
            # field definition. That saves us the trouble of having to
            # convert it ourselves.
            kwargs['validate_default'] = True

        elif not self.required:
            kwargs['default'] = None

        # the validator will be added to the model class during model
        # creation, it's not associated directly with the field
        # definition.

        self._field_info = Field(**kwargs)  # type: ignore


class TemplateModelDefinition(SubModel):
    """
    YAML definition for creating a Pydantic model for template data
    validation
    """

    name: str = Field(alias='name', default='model')
    description: Optional[str] = Field(alias='description', default=None)
    fields: Dict[str, TemplateFieldDefinition] = Field(
        alias='fields', default_factory=dict)

    _model_class: Optional[Type[BaseModel]] = PrivateAttr(default=None)


    def model_post_init(self, __context: Any):
        super().model_post_init(__context)

        field_defs: Dict[str, Any] = {
            name: field.definition for name, field in self.fields.items()
        }
        field_defs['__base__'] = (LocalMixin, BaseModel)

        validators = {}
        for name, field in self.fields.items():
            if field.validation:
                validators[f"validate_{name}"] = \
                    field.validation.as_field_validator(name)
        if validators:
            field_defs['__validators__'] = validators

        self._model_class = create_model(  # type: ignore
            self.name, **field_defs)


    def get_model_class(self) -> Type[BaseModel]:
        """
        Get the model class for the template model.
        """

        if not self._model_class:
            raise ValueError(f"Model class not created for {self.name}")
        return self._model_class


    def new(self, data: Dict[str, Any]) -> BaseModel:
        """
        Create a new instance of the template model from the given data.
        """

        if not self._model_class:
            raise ValueError(f"Model class not created for {self.name}")

        return self._model_class.model_validate(data)


class Template(BaseModel, IdentifiableMixin, LocalMixin):
    """
    A Template allows for the expansion of some YAML data into zero or
    more YAML docs, via Jinja2
    """

    typename: ClassVar[str] = "template"

    defaults: Dict[str, Any] = Field(alias='defaults', default_factory=dict)

    template_file: Optional[str] = Field(alias='file', default=None)
    template_content: Optional[str] = Field(alias='content', default=None)
    template_model: Optional[TemplateModelDefinition] = Field(
        alias='model', default=None)

    description: Optional[str] = Field(alias='description', default=None)

    _undeclared: Set[str] = PrivateAttr(default=None)
    _jinja2_template: Jinja2Template = PrivateAttr(default=None)
    _base_path: Optional[Path] = PrivateAttr(default=None)


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
            extensions=['jinja2.ext.do', 'jinja2.ext.loopcontrols'],
            undefined=StrictUndefined)

        try:
            if self.template_content:
                if self.template_file:
                    raise TemplateError(
                        original_error=ValueError(
                            "Template content is not allowed when template file is specified"),
                        template=self)

                ast = jinja_env.parse(self.template_content)

            else:
                if not self.template_file:
                    raise TemplateError(
                        original_error=ValueError(
                            "Template content is required when template file is not specified"),
                        template=self)

                elif Path(self.template_file).is_absolute():
                    raise TemplateError(
                        original_error=ValueError(
                            "Absolute paths are not allowed with template file loading"
                        ),
                        template=self)

                src = loader.get_source(jinja_env, self.template_file)[0]
                ast = jinja_env.parse(src)

        except Jinja2TemplateSyntaxError as e:
            raise TemplateSyntaxError(
                original_error=e,
                template=self,
                template_file=self.template_file) from e

        except Jinja2TemplateError as e:
            raise TemplateError(
                original_error=e,
                template=self,
                template_file=self.template_file) from e

        self._undeclared = find_undeclared_variables(ast)
        self._jinja2_template = jinja_env.from_string(ast)


    def get_missing(self):
        """
        Return the set of variable names which are referenced in the Jinja2
        template, but which are not defined in the defaults
        """

        return self._undeclared.difference(self.defaults)


    def validate_call(self, data: Dict[str, Any]) -> bool:
        """
        Validate the call data against the template model if configured.
        """

        if not self.template_model:
            return True
        return bool(self.template_model.new(data))


    def render(self, data: Dict[str, Any]) -> str:
        """
        Render the template with the given data into a str
        """

        if self.defaults:
            data = dict(self.defaults, **data)

        tmodel = self.template_model
        if tmodel:
            call_model = tmodel.new(data)
            model_name = tmodel.name or 'model'
            render_data = {model_name: call_model, '_data': data}
        else:
            render_data = dict(data, _data=data)

        try:
            return self._jinja2_template.render(**render_data)

        except UndefinedError as e:
            raise TemplateRenderError(
                original_error=e,
                template=self,
                data=data) from e


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
            trace = list(trace)
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
                        rendered_content=rendered)
                obj.update(merge)
                yield obj

        except yaml.YAMLError as e:
            raise TemplateOutputError(
                message=f"Template rendered invalid YAML: {e}",
                template=self,
                data=data,
                rendered_content=rendered,
                original_exception=e) from e


    def render_call(self, call: TemplateCall):
        return self.render_and_load(call.data)


class MultiTemplate(Template):
    """
    A MultiTemplate is a template that generates multiple YAML documents.
    """

    typename: ClassVar[str] = "multi"

    def __init__(self):
        super().__init__(name='multi', content="#")


    def render_call(self, call: TemplateCall) -> Iterator[Dict[str, Any]]:
        data = call.data
        data.pop('type', None)

        trace = data.get('__trace__', ())
        trace = list(trace)
        trace.append({
            'name': 'multi',
            'file': None,
            'line': None,
        })

        filename = data.get('__file__')

        for key, value in data.items():
            if key.startswith('_') or key.startswith('x-'):
                continue

            if not value:
                continue

            if isinstance(value, dict):
                if 'name' not in value:
                    value['name'] = key
                value['__trace__'] = trace
                value['__file__'] = filename

                yield value

            else:
                logger.debug(f"stray key:value in multi: f{key}:f{value!r}")


# The end.
