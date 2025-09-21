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


import logging
from collections import OrderedDict
from enum import Enum, auto
from typing import Any, Dict, Iterator, Optional, List, OrderedDict, Type

from .templates import Template, TemplateCall
from .models import CORE_MODELS, Base, RawObject


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
        obj: Any,
        redefine: Redefine = Redefine.ERROR,
        logger: Optional[logging.Logger] = None):

    orig = into.get(key, None)

    if orig is None:
        into[key] = obj
        return
    elif orig is obj:
        return

    # Oh no, we're in redefine territory

    if redefine == Redefine.IGNORE:
        return

    if redefine == Redefine.ALLOW:
        into[key] = obj
        return

    stmt = f"{key} at {obj.filepos()} (original {orig.filepos()})"
    logger = logger or default_logger

    if redefine == Redefine.ERROR:
        raise NamespaceRedefine(f"Redefinition of {stmt}")

    elif redefine == Redefine.IGNORE_WARN:
        logger.warning(f"Ignored redefinition of {stmt}")

    elif redefine == Redefine.ALLOW_WARN:
        logger.warning(f"Redefined {stmt}")
        into[key] = obj

    else:
        # should never be reached, but just in case...
        assert False, f"Unknown redefine setting {redefine!r}"


class NamespaceRedefine(Exception):
    pass


class ExpansionError(Exception):
    pass


class Namespace:

    def __init__(
            self,
            coretypes: List[Type[Base]] = CORE_MODELS,
            enable_templates: bool = True,
            redefine: Redefine = Redefine.ERROR,
            logger: Optional[logging.Logger] = None):

        self.redefine = redefine
        self.logger = logger or default_logger

        # mapping of type names to classes. The special mapping of None
        # indicates the class to be used when nothing else matches. This
        # is normally a TemplateCall
        self.typemap = {}

        for tp in coretypes:
            self.typemap[tp.typename] = tp

        if enable_templates:
            self.typemap["template"] = Template
            self.typemap[None] = TemplateCall

        # a sequence of un-processed objects to be added into this
        # namespace
        self._feedline = []

        # the actual namespace storage, mapping
        #  `(obj.typename, obj.name): obj`
        self._ns = {}

        # templates, mapping simply as `tmpl.name: tmpl`
        self._templates = {}

        # if we're finding templates recursively expanding to templates,
        # only allow that nonsense 100 deep then error
        self.max_depth = 100


    def to_object(self, objdict):
        objtype = objdict.get('type')
        if objtype is None:
            raise ValueError("Object data has no type set")

        cls = self.typemap.get(objtype) or self.typemap.get(None)
        if cls is None:
            raise ValueError(f"No type handler for {objtype}")

        return cls(objdict)


    def to_objects(self, objseq):
        return map(self.to_object, objseq)


    def add(self, obj):
        if isinstance(obj, (Template, TemplateCall)):
            raise TypeError(f"{type(obj).__name__} cannot be"
                            " directly added to a Namespace")

        return add_into(self._ns, obj.key(), obj,
                         self.redefine, self.logger)


    def add_template(self, template: Template):
        if not isinstance(template, Template):
            raise TypeError("add_template requires a Template instance")

        return add_into(self._templates, template.name, template,
                         self.redefine, self.logger)


    def feed_raw(self, data):
        return self.feed(self.to_object(data))


    def feedall_raw(self, datasequence):
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


    def expand(self):
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
                msg = f"Could not resolve template: {call.typename}"
                raise ExpansionError(msg)


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

        acted = False

        for obj in sequence:
            if isinstance(obj, Template):
                self.add_template(obj)
                acted = True

            elif isinstance(obj, TemplateCall):

                templ = self._templates.get(obj.typename)
                if not templ:
                    # defer for another pass
                    deferals.append(obj)

                else:
                    # attempt to expand the call. If there are existing
                    # deferals, then the expansion will just be inlined
                    # into the deferals. If not, then the expansion will
                    # be added
                    self._expand(self.to_objects(templ.render_call(obj)),
                                 deferals, depth=depth+1)
                    acted = True

            else:
                if deferals:
                    deferals.append(obj)
                else:
                    self.add(obj)
                    acted = True

        return acted


class TemplateNamespace(Namespace):

    def __init__(
            self,
            coretypes: List[Type[Base]] = CORE_MODELS,
            redefine: Redefine = Redefine.ERROR,
            logger: Optional[logging.Logger] = None):

        super().__init__(
            coretypes=coretypes,
            enable_templates=True,
            redefine=redefine,
            logger=logger)

        # we need to know what to skip, because the default is to
        # assume it's a TemplateCall
        self.ignored_types = set(tp.typename for tp in coretypes)


    def to_objects(self, dataseq) -> Iterator[Base]:
        # updated to chop out the None values that our to_object will
        # return for ignored_types
        return filter(None, map(self.to_object, dataseq))


    def to_object(self, data):
        if data['type'] in self.ignored_types:
            return None
        return super().to_object(data)


    def add(self, obj):
        # We don't actually record any real objects in the TemplateNamespace
        pass


class ExpanderNamespace(Namespace):

    def __init__(
        self,
        coretypes: List[Type[Base]] = CORE_MODELS,
        redefine: Redefine = Redefine.ERROR,
        logger: Optional[logging.Logger] = None):

        super().__init__(
            coretypes=(),
            enable_templates=True,
            redefine=redefine,
            logger=logger)

        faketypes = {tp.typename: RawObject for tp in coretypes}
        faketypes['template'] = Template
        faketypes[None] = TemplateCall
        self.typemap = faketypes


# The end.
