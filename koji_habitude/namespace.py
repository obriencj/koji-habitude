"""
koji_habitude.namespace

A Namespace is a platform for converting YAML documents into instances
of core types. It controls the direct unmarshaling, as well as the
resolution logic for defining and expanding templates.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


from enum import Enum, auto
import logging
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
)

from pydantic import ValidationError as PydanticValidationError

from .models import Base, BaseKey, BaseObject, CORE_MODELS
from .templates import Template, TemplateCall
from .exceptions import (
    ValidationError,
    ExpansionError,
    RedefineError,
)


__all__ = (
    'Namespace',
    'TemplateNamespace',
    'ExpanderNamespace',
    'Redefine',
)


default_logger = logging.getLogger(__name__)


class Redefine(Enum):

    """
    Represents the options for how we want `Namespace.add` and
    `Namespace.add_template` to behave when the newly added item
    conflicts with a previously added entry
    """

    ERROR = auto()
    """
    this means redefinition raises an exception
    """

    IGNORE = auto()
    """
    this means redefinition is ignored
    """

    IGNORE_WARN = auto()
    """
    this means redefinition is ignored but produces a warning
    """

    ALLOW = auto()
    """
    this means redefinition is allowed
    """

    ALLOW_WARN = auto()
    """
    this means redefinition is allowed but produces a warning
    """


def add_into(
        into: Dict,
        key: Any,
        obj: Base,
        redefine: Redefine = Redefine.ERROR,
        logger: Optional[logging.Logger] = None) -> None:

    """
    Add an object into a dictionary, handling redefinition.

    Args:
        into: The dictionary to add the object into
        key: The key to add the object under
        obj: The object to add
        redefine: The redefine setting
        logger: The logger to use when redefine is IGNORE_WARN or ALLOW_WARN

    Raises:
        RedefineError: If the object is being redefined and the redefine setting is ERROR
        AssertionError: If the redefine setting is unknown
    """

    orig = into.get(key)

    if orig is None:
        into[key] = obj
        return
    elif orig is obj:
        return

    # Oh no, we're in redefine territory

    if redefine == Redefine.IGNORE:
        # ignore the attempt at redefinition, do nothing
        return

    if redefine == Redefine.ALLOW:
        # allow the redefinition, update the value
        into[key] = obj
        return

    # prepare a statement to be used in the other cases
    stmt = f"{key} at {obj.filepos_str()} (original {orig.filepos_str()})"
    logger = logger or default_logger

    if redefine == Redefine.ERROR:
        raise RedefineError(key, orig, obj)

    elif redefine == Redefine.IGNORE_WARN:
        logger.warning(f"Ignored redefinition of {stmt}")

    elif redefine == Redefine.ALLOW_WARN:
        logger.warning(f"Redefined {stmt}")
        into[key] = obj

    else:
        # should never be reached, but just in case...
        assert False, f"Unknown redefine setting {redefine!r}"


def merge_into(
        into: Dict,
        other: Dict,
        redefine: Redefine = Redefine.ERROR,
        logger: Optional[logging.Logger] = None) -> None:
    """
    Merge a dictionary into another dictionary, following the redefine semantics.
    """
    for key, obj in other.items():
        add_into(into, key, obj, redefine, logger)


class Namespace:

    def __init__(
            self,
            coretypes: Union[Dict[str, Type[Base]], Sequence[Type[Base]]] = CORE_MODELS,
            enable_templates: bool = True,
            redefine: Redefine = Redefine.ERROR,
            logger: Optional[logging.Logger] = None):

        self.redefine = redefine
        self.logger = logger or default_logger

        # mapping of type names to classes. The special mapping of None
        # indicates the class to be used when nothing else matches. This
        # is normally a TemplateCall
        if isinstance(coretypes, Mapping):
            coretypes = dict(coretypes)
        else:
            coretypes = {tp.typename: tp for tp in coretypes}
        self.typemap: Dict[Optional[str], Type[Base]] = coretypes

        if enable_templates:
            self.typemap["template"] = Template
            self.typemap[None] = TemplateCall

        # a sequence of un-processed objects to be added into this
        # namespace
        self._feedline: List[Base] = []

        # the actual namespace storage, mapping
        #  `(obj.typename, obj.name): obj`
        self._ns: Dict[BaseKey, Base] = {}

        # templates, mapping simply as `tmpl.name: tmpl`
        self._templates: Dict[str, Template] = {}

        # if we're finding templates recursively expanding to templates,
        # only allow that nonsense 100 deep then error
        self.max_depth: int = 100


    def keys(self) -> Iterator[BaseKey]:
        """
        Return an iterator over the keys in the namespace.
        """

        return self._ns.keys()


    def items(self) -> Iterator[Tuple[BaseKey, Base]]:
        """
        Return an iterator over the items in the namespace.
        """

        return self._ns.items()


    def values(self) -> Iterator[Base]:
        """
        Return an iterator over the values in the namespace.
        """

        return self._ns.values()


    def get(self, key: BaseKey, default: Any = None) -> Optional[Base]:
        """
        Return the object in the namespace with the given key.
        """

        return self._ns.get(key, default)


    def templates(self) -> Iterator[Template]:
        """
        Return an iterator over the templates in the namespace.
        """

        return self._templates.values()


    def get_template(self, name: str) -> Optional[Template]:
        """
        Return the template in the namespace with the given name.
        """
        return self._templates.get(name)


    def merge_templates(
        self,
        other: 'Namespace',
        redefine: Optional[Redefine] = None) -> None:
        """
        Merge the templates from another namespace into this one, following the
        redefine semantics of this namespace. If redefine is provided, use those
        rules instead.
        """
        redefine = redefine or self.redefine
        merge_into(self._templates, other._templates, redefine, self.logger)


    def get_type(self, typename: str, or_call: bool = True) -> Optional[Type[Base]]:
        """
        Return the type for the given typename. If or_call is True (the
        default), will return a TemplateCall for missing type names. If or_call
        is False, or if the Namespace was not created with templates enabled,
        then this will return None for missing type names.
        """
        if or_call:
            return self.typemap.get(typename) or self.typemap.get(None)
        else:
            return self.typemap.get(typename)


    def to_object(self, objdict: Dict[str, Any]) -> Base:
        """
        Convert a dictionary into a Base object instance. Types are resolved
        from the `type` key. An exception is raised if no type key is present.

        If templates are enabled, then the `type` key may be `template` in order
        to define a new template. Any other unknown type is assumed to be a
        template call.

        If templates are not enabled, then any unknown type is an error.

        Raises:
            ValueError: If no type key is present, or if no type handler is
            found for the type
            ValidationError: If pydantic validation fails for the object
        """

        objtype = objdict.get('type')
        if objtype is None:
            raise ValueError("Object data has no type set")

        cls = self.get_type(objtype)
        if cls is None:
            raise ValueError(f"No type handler for {objtype}")

        try:
            return cls.from_dict(objdict)
        except PydanticValidationError as e:
            raise ValidationError(
                original_error=e,
                objdict=objdict,
            ) from e


    def to_objects(self, objseq: Sequence[Dict[str, Any]]) -> Iterator[Base]:
        """
        Convert a sequence of dictionaries into a sequence of Base object
        instances, via the `to_object` method.
        """

        return map(self.to_object, objseq)


    def add(self, obj: Base) -> None:
        """
        Add an object to the namespace. This is called during the `expand`
        method as objects are loaded from the feed queue.

        Raises:
            TypeError: If the object is a Template or TemplateCall
        """

        if isinstance(obj, (Template, TemplateCall)):
            raise TypeError(f"{type(obj).__name__} cannot be"
                            " directly added to a Namespace")

        return add_into(self._ns, obj.key(), obj,
                         self.redefine, self.logger)


    def add_template(self, template: Template):
        """
        Add a template to the namespace. This is called during the `expand`
        method as templates are loaded from the feed queue.

        Raises:
            TypeError: If the object is not a Template
        """
        if not isinstance(template, Template):
            raise TypeError("add_template requires a Template instance")

        return add_into(self._templates, template.name, template,
                         self.redefine, self.logger)


    def feed_raw(self, data: Dict[str, Any]) -> None:
        """
        Add raw data to the queue of objects to be added to this namespace. The
        data will be converted to an object via the `to_object` method. This
        queue is processed via the `expand()` method.
        """

        return self.feed(self.to_object(data))


    def feedall_raw(self, datasequence: Sequence[Dict[str, Any]]) -> None:
        """
        Add a sequence of raw data to the queue of objects to be added to this
        namespace. The data will be converted to an object via the `to_object`
        method. This queue is processed via the `expand()` method.
        """

        return self.feedall(self.to_objects(datasequence))


    def feed(self, obj):
        """
        Appends an object to the queue of objects to be added to this
        namespace. This queue is processed via the `expand()` method.
        """

        return self._feedline.append(obj)


    def feedall(self, sequence):
        """
        Appends all objects in sequence into the queue of objects
        to be added to this namespace. This queue is processed via the
        `expand()` method.
        """

        return self._feedline.extend(sequence)


    def expand(self) -> None:
        """
        Process the queue of objects that have been fed into this namespace via
        the `feed` or `feedall` methods. At this point any templates in the
        queue will be added to the namespace, and any template calls will be
        expanded. This is the final step in the loading process.

        The redefine semantics are applied as objects are processed, so this
        method will raise an exception if a redefinition is encountered and the
        redefine setting is `ERROR`.

        Raises:
            ExpansionError: If the maximum depth is reached when attempting to
            expand a recursively expanding template

            AssertionError: If the first deferal is not a TemplateCall when
            no further objects can be added to the namespace (indicates a bug)
        """

        work = self._feedline
        while work:
            deferals = []
            if self._expand(work, deferals):
                work = self._feedline = deferals

            else:
                # blame it on the first deadlock, which ought to be
                # the first deferal, which would have to be a TemplateCall
                call = deferals[0]
                assert isinstance(call, TemplateCall)
                raise ExpansionError(
                    call=call,
                    available_templates=list(self._templates.keys()),
                )


    def _expand(self, sequence, deferals, depth=0):

        # processes the sequence in order, either adding core objects
        # or templates to the namespace. If it hits a TemplateCall,
        # then attempts to expand that template and process its
        # expansion via recursion. If the TemplateCall cannot be expanded,
        # we defer, and all further core objects, expanded TemplateCalls,
        # and unexpandable TemplateCalls are fed into the deferals list.
        # So long as we invoked at least one .add or .add_template, we
        # have impacte the namespace, and therefore we'll have the
        # deferals fed back to us in another call.

        # In this manner, all left-most available items are processed
        # until a roadblock is hit. Template definitions will be pulled
        # from what's available, and in this manner if we encounter
        # a TemplateCall we cannot act on now, we can hope to act on it
        # later on.

        if depth > self.max_depth:
            raise ExpansionError(f"Maximum depth of {self.max_depth} reached")

        # acted is a deadlock check. We need to have done at least one of the
        # following actions to not be in a deadlock:
        # 1. Added a template
        # 2. Expanded a template call
        # 3. Added an object
        acted = False

        for obj in sequence:
            if isinstance(obj, Template):
                self.add_template(obj)
                acted = True

            elif isinstance(obj, TemplateCall):

                templ = self._templates.get(obj.typename)
                if not templ:
                    # template not defined (yet?) defer for another pass
                    deferals.append(obj)

                else:
                    # attempt to expand the call. If there are existing
                    # deferals, then the expansion will just be inlined
                    # into the deferals. If not, then the expansion will
                    # be added

                    expanded = self.to_objects(templ.render_call(obj))

                    if deferals:
                        # We're not allowing templates that might have
                        # been expanded in here to be added, nor are
                        # we re-expanding any nested calls. We want to
                        # give any earlier deferred calls a change to
                        # expand and potentially add their templates
                        # first. This ensures a more consistent
                        # ordering, where we prefer to add templates
                        # from earlier on, even when they are expanded
                        # from other templates.
                        deferals.extend(expanded)
                    else:
                        self._expand(expanded, deferals, depth=depth+1)
                    acted = True

            else:
                if deferals:
                    # we want to enforce some ordering, so if we are already
                    # deferring, we need to give earlier calls a chance to
                    # expand and add first.
                    deferals.append(obj)
                else:
                    self.add(obj)
                    acted = True

        return acted


class TemplateNamespace(Namespace):
    """
    A namespace that only allows templates to be added and expanded. Discards
    all other objects.
    """

    def __init__(
            self,
            coretypes: Union[Dict[str, Type[Base]], Sequence[Type[Base]]] = CORE_MODELS,
            redefine: Redefine = Redefine.ERROR,
            logger: Optional[logging.Logger] = None):

        super().__init__(
            coretypes=coretypes,
            enable_templates=True,
            redefine=redefine,
            logger=logger)

        # we need to know what to skip, because the default is to
        # assume it's a TemplateCall
        if isinstance(coretypes, Mapping):
            ignores = set(coretypes)
        else:
            ignores = {tp.typename for tp in coretypes}
        self.ignored_types: Set[str] = ignores


    def to_objects(self, dataseq: Sequence[Dict[str, Any]]) -> Iterator[Base]:
        # updated to chop out the None values that our to_object will
        # return for ignored_types
        return filter(None, map(self.to_object, dataseq))


    def to_object(self, data: Dict[str, Any]) -> Optional[Base]:
        if data['type'] in self.ignored_types:
            return None
        return super().to_object(data)


    def add(self, obj: Base) -> None:
        """
        Does nothing in this subclass
        """
        pass


class ExpanderNamespace(Namespace):
    """
    A namespace that expands all core types to basic BaseObject instances. This
    avoids schema validation, and enables us to guarantee template expansion.
    Useful for when a user want to see the raw expanded output of their
    templates.
    """

    def __init__(
        self,
        coretypes: Union[Dict[str, Type[Base]], Sequence[Type[Base]]]= CORE_MODELS,
        redefine: Redefine = Redefine.ERROR,
        logger: Optional[logging.Logger] = None):

        if isinstance(coretypes, Mapping):
            faketypes = {tn: BaseObject for tn in coretypes}
        else:
            faketypes = {tp.typename: BaseObject for tp in coretypes}

        super().__init__(
            coretypes=faketypes,
            enable_templates=True,
            redefine=redefine,
            logger=logger)


# The end.
