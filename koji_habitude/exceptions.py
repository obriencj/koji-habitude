"""
koji_habitude.exceptions

Exception hierarchy for wrapping third-party exceptions with context about
the YAML file, object, template, or change that caused the error.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated


from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from jinja2.exceptions import TemplateError as Jinja2TemplateError
from jinja2.exceptions import TemplateSyntaxError as Jinja2TemplateSyntaxError
from jinja2.exceptions import UndefinedError as Jinja2UndefinedError
from pydantic import ValidationError as PydanticValidationError


__all__ = (
    'HabitudeError',
    'YAMLError',
    'ValidationError',
    'TemplateError',
    'TemplateSyntaxError',
    'TemplateRenderError',
    'TemplateOutputError',
    'KojiError',
    'ChangeReadError',
    'ChangeApplyError',
    'ExpansionError',
    'RedefineError',
)


class HabitudeError(Exception):
    """
    Base exception for all koji-habitude exceptions.

    All custom exceptions include context about where the error originated.

    :param message: The error message
    :param filename: Optional filename where the error occurred
    :param lineno: Optional line number where the error occurred
    :param trace: Optional template trace information
    :param original_exception: Optional original exception that caused this error
    """

    def __init__(
            self,
            message: str,
            filename: Optional[str] = None,
            lineno: Optional[int] = None,
            trace: Optional[List[Dict[str, Any]]] = None,
            original_exception: Optional[Exception] = None):

        self.message = message
        self.filename = filename
        self.lineno = lineno
        self.trace = trace or []
        self.original_exception = original_exception

        # Build comprehensive error message
        full_message = self._format_message()
        super().__init__(full_message)


    def _format_message(self) -> str:
        """
        Format the complete error message with context.

        :returns: Formatted error message with location, trace, and original exception info
        """

        parts = [self.message]

        # Add location information
        if self.filename:
            location = self.filename
            if self.lineno:
                location = f"{location}:{self.lineno}"
            parts.append(f"  Location: {location}")

        # Add trace information (from template expansion)
        if self.trace:
            parts.append("  Template trace:")
            for t in self.trace:
                name = t.get('name', '<unknown>')
                file = t.get('file', '<unknown>')
                line = t.get('line')
                if line:
                    parts.append(f"    - {name} in {file}:{line}")
                else:
                    parts.append(f"    - {name} in {file}")

        # Add original exception info
        if self.original_exception:
            exc_type = type(self.original_exception).__name__
            parts.append(f"  Original error: {exc_type}: {self.original_exception}")

        return "\n".join(parts)


class YAMLError(HabitudeError):
    """
    Wraps YAML parsing errors with file context.

    Used when YAML files cannot be parsed due to syntax errors.

    :param original_error: The original YAML error
    :param filename: Optional filename where the error occurred
    """

    def __init__(
            self,
            original_error: yaml.YAMLError,
            filename: Optional[str] = None):
        # Extract line number from YAML error if available
        lineno = None
        if hasattr(original_error, 'problem_mark'):
            lineno = original_error.problem_mark.line + 1

        message = f"YAML parsing error: {original_error}"

        super().__init__(
            message=message,
            filename=filename,
            lineno=lineno,
            original_exception=original_error,
        )


class ValidationError(HabitudeError):
    """
    Wraps pydantic validation errors with object and file context.

    Used when object data fails pydantic schema validation.

    :param original_error: The original pydantic validation error
    :param objdict: The object data that failed validation
    """

    def __init__(
            self,
            original_error: PydanticValidationError,
            objdict: Dict[str, Any]):

        self.data = objdict

        typename = objdict.get('type')
        name = objdict.get('name')
        self.typename = typename
        self.name = name

        # Build a clear message
        obj_desc = f"{typename} '{name}'" if typename and name else "object"
        message = f"Validation error for {obj_desc}"

        # Add validation details
        error_count = len(original_error.errors())
        message += f" ({error_count} validation error{'s' if error_count > 1 else ''}):"

        for err in original_error.errors():
            field = '.'.join(str(x) for x in err['loc'])
            msg = err['msg']
            message += f"\n  - {field}: {msg}"

        super().__init__(
            message=message,
            filename=objdict.get('__file__'),
            lineno=objdict.get('__line__'),
            trace=objdict.get('__trace__'),
            original_exception=original_error,
        )


class TemplateError(HabitudeError):
    """
    Wraps Jinja2 template errors with template context.

    Base class for all template-related errors.

    :param original_error: The original exception
    :param template: Optional template object
    :param data: Optional call data
    :param template_file: Optional template filename
    """

    def __init__(
            self,
            original_error: Exception,
            template: Any = None,  # Template object
            data: Optional[Dict[str, Any]] = None,  # Call data
            template_file: Optional[str] = None):

        # Extract context from template if provided
        if template:
            self.template_name = template.name
            template_filename = template.filename
            template_lineno = template.lineno
        else:
            self.template_name = None
            template_filename = None
            template_lineno = None

        # Extract context from call data if provided
        if data:
            call_filename = data.get('__file__')
            call_lineno = data.get('__line__')
            trace = data.get('__trace__')
        else:
            call_filename = None
            call_lineno = None
            trace = None

        self.template_file = template_file
        self.call_filename = call_filename
        self.call_lineno = call_lineno

        # Determine which file/line to use
        filename = template_filename or call_filename
        lineno = template_lineno or call_lineno

        # Build message
        template_desc = f"template '{self.template_name}'" if self.template_name else "template"
        message = f"Error in {template_desc}: {original_error}"

        if template_file:
            message += f"\n  Template file: {template_file}"

        super().__init__(
            message=message,
            filename=filename,
            lineno=lineno,
            trace=trace,
            original_exception=original_error,
        )


class TemplateSyntaxError(TemplateError):
    """
    Wraps Jinja2 syntax errors.

    Used when template content has invalid Jinja2 syntax.

    :param original_error: The original Jinja2 syntax error
    :param template: The template object
    :param template_file: Optional template filename
    """

    def __init__(
            self,
            original_error: Exception,
            template: Any,  # Template object
            template_file: Optional[str] = None):

        super().__init__(
            original_error=original_error,
            template=template,
            template_file=template_file,
        )

        # Try to extract line number from jinja2 error
        jinja_lineno = None
        if hasattr(original_error, 'lineno'):
            jinja_lineno = original_error.lineno

        if jinja_lineno:
            self.message += f"\n  Template line: {jinja_lineno}"


class TemplateRenderError(TemplateError):
    """
    Wraps Jinja2 rendering errors (undefined variables, etc.).

    Used when template rendering fails due to missing variables or other
    runtime issues.

    :param original_error: The original rendering error
    :param template: The template object
    :param data: The call data
    """

    def __init__(
            self,
            original_error: Exception,
            template: Any,  # Template object
            data: Dict[str, Any]):

        super().__init__(
            original_error=original_error,
            template=template,
            data=data,
        )


class TemplateOutputError(HabitudeError):
    """
    Used when template renders successfully but produces invalid output.

    This can be either invalid YAML or valid YAML that fails validation.

    :param message: Error message describing the problem
    :param template: The template object
    :param data: The call data
    :param rendered_content: Optional rendered content
    :param original_exception: Optional original exception
    """

    def __init__(
            self,
            message: str,
            template: Any,  # Template object
            data: Dict[str, Any],
            rendered_content: Optional[str] = None,
            original_exception: Optional[Exception] = None):

        self.template_name = template.name
        self.rendered_content = rendered_content

        # Build message
        template_desc = f"template '{template.name}'" if template.name else "template"
        full_message = f"Invalid output from {template_desc}: {message}"

        super().__init__(
            message=full_message,
            filename=template.filename or data.get('__file__'),
            lineno=template.lineno or data.get('__line__'),
            trace=data.get('__trace__'),
            original_exception=original_exception,
        )


class KojiError(HabitudeError):
    """
    Wraps generic koji exceptions with object context.

    Used when koji API calls fail.

    :param original_error: The original koji error
    :param typename: Optional type name of the object
    :param name: Optional name of the object
    :param filename: Optional filename
    :param lineno: Optional line number
    :param trace: Optional template trace
    :param operation: Optional operation description
    :param method_name: Optional koji method name
    :param parameters: Optional parameters passed to the method
    """

    def __init__(
            self,
            original_error: Exception,
            typename: Optional[str] = None,
            name: Optional[str] = None,
            filename: Optional[str] = None,
            lineno: Optional[int] = None,
            trace: Optional[List[Dict[str, Any]]] = None,
            operation: Optional[str] = None,
            method_name: Optional[str] = None,
            parameters: Optional[Dict[str, Any]] = None):

        self.typename = typename
        self.name = name
        self.operation = operation
        self.method_name = method_name
        self.parameters = parameters

        # Build message
        obj_desc = f"{typename} '{name}'" if typename and name else "object"

        if operation:
            message = f"Koji error during {operation} for {obj_desc}"
        else:
            message = f"Koji error for {obj_desc}"

        if method_name:
            message += f"\n  Koji method: {method_name}"
            if parameters:
                message += f"\n  Parameters: {parameters}"

        message += f"\n  Error: {original_error}"

        super().__init__(
            message=message,
            filename=filename,
            lineno=lineno,
            trace=trace,
            original_exception=original_error,
        )


class ChangeReadError(KojiError):
    """
    Wraps koji exceptions that occur during the query/read phase.

    :param original_error: The original koji error
    :param obj: The object being queried
    """

    def __init__(
            self,
            original_error: Exception,
            obj: Any):

        super().__init__(
            original_error=original_error,
            typename=obj.typename,
            name=obj.name,
            filename=obj.filename,
            lineno=obj.lineno,
            trace=getattr(obj, 'trace', None),
            operation='query',
        )


class ChangeApplyError(KojiError):
    """
    Wraps koji exceptions that occur during the apply/write phase.

    :param original_error: The original koji error
    :param obj: The object being modified
    :param change_description: Optional description of the change
    :param method_name: Optional koji method name
    :param parameters: Optional parameters passed to the method
    """

    def __init__(
            self,
            original_error: Exception,
            obj: Any,  # Base object
            change_description: Optional[str] = None,
            method_name: Optional[str] = None,
            parameters: Optional[Dict[str, Any]] = None):

        self.change_description = change_description

        super().__init__(
            original_error=original_error,
            typename=obj.typename,
            name=obj.name,
            filename=obj.filename,
            lineno=obj.lineno,
            trace=getattr(obj, 'trace', None),
            operation='apply changes',
            method_name=method_name,
            parameters=parameters,
        )

        if change_description:
            self.message += f"\n  Change: {change_description}"


class ExpansionError(HabitudeError):
    """
    Indicates an error during the template expansion process.

    :param call: Either a `:class:TemplateCall` object or a plain string message
    :param available_templates: Optional list of available template names
    """

    def __init__(
            self,
            call: Any,  # TemplateCall object or string message
            available_templates: Optional[List[str]] = None):

        # Handle both TemplateCall objects and plain string messages
        if isinstance(call, str):
            # Plain message (e.g., "Maximum depth reached")
            message = call
            self.template_name = None
            filename = None
            lineno = None
            trace = None
        else:
            # TemplateCall object
            self.template_name = call.template_name
            message = f"Could not resolve template: {call.template_name}"
            if available_templates:
                message += f"\n  Available templates: {', '.join(sorted(available_templates))}"
            filename = call.filename
            lineno = call.lineno
            trace = call.trace

        self.available_templates = available_templates

        super().__init__(
            message=message,
            filename=filename,
            lineno=lineno,
            trace=trace,
        )


class RedefineError(HabitudeError):
    """
    Indicates a redefinition of an object in the namespace.

    :param key: Either a `BaseKey` (tuple) or string (for templates)
    :param original_obj: The original object
    :param new_obj: The new object attempting to redefine
    """

    def __init__(
            self,
            key: Any,  # BaseKey (tuple) or string (for templates)
            original_obj: Any,  # Base
            new_obj: Any):
        self.key = key
        self.original_obj = original_obj
        self.new_obj = new_obj

        # Handle both BaseKey tuples and simple string keys (for templates)
        if isinstance(key, tuple) and len(key) == 2:
            typename, name = key
            message = f"Redefinition of {typename} '{name}'"
        else:
            # Simple string key (like template names)
            message = f"Redefinition of '{key}'"

        message += f"\n  Original: {original_obj.filepos_str()}"
        message += f"\n  New: {new_obj.filepos_str()}"

        super().__init__(
            message=message,
            filename=new_obj.filename,
            lineno=new_obj.lineno,
            trace=getattr(new_obj, 'trace', None),
        )


# The end.
