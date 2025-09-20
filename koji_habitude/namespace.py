"""
koji_habitude.namespace

A Namespace is a platform for converting YAML documents into instances
of core types. It controls the direct unmarshaling, as well as the
resolution logic for defining and expanding templates.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
"""

# Vibe-Coding State: Pure Human


import logging
from enum import Enum, auto
from typing import Any, Dict, Iterator, Optional

from .template import Template, TemplateCall


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


def _add_into(
        into: Dict,
        key: Any,
        obj: Any,
        redefine: Redefine = Redefine.ERROR,
        logger: Optional[Logger] = None):

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
        logger.warn(f"Ignored redefinition of {stmt}")

    elif redef == Redefine.ALLOW_WARN:
        logger.warn(f"Redefined {stmt}")
        self._ns[key] = obj

    else:
        assert False, f"Unhandled redefine value {redef}"


class Namespace:

    def __init__(self, redefine=Redefine.ERROR, logger=None):

        self.redefine = redefine
        self.logger = logger or default_logger

        # mapping of type names to classes. The special mapping of None
        # indicates the class to be used when nothing else matches. This
        # is normally a TemplateCall
        self.typemap = {}

        # a sequence of un-processed objects to be added into this
        # namespace
        self._feedline = []

        # the actual namespace storage, mapping
        #  `(obj.typename, obj.name): obj`
        self._ns = {}

        # templates, mapping simply as `tmpl.name: tmpl`
        self._templates = {}


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

        return _add_into(self._ns, obj.key(), obj,
                         self.redefine, self.logger)


    def add_template(self, template: Template):
        if not isinstance(template, Template):
            raise TypeError("add_template requires a Template instance")

        return _add_into(self._templates, template.name, template,
                         self.redefine, self.logger)


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
                raise ValueError(msg)


    def _expand(self, sequence, deferals):

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

        acted = False

        coretypes = self._coretypes
        for obj in sequence:
            if isinstance(obj, coretypes):
                if deferals:
                    deferals.append(obj)
                else:
                    self.add(obj)

                    # Let's actually not consider this as impacting how
                    # we consider deferals. Just because we added a core
                    # type doesn't mean we've moved closer to being able
                    # to resolve any unresolved TemplateCalls

                    # acted = True

            elif isinstance(obj, Template):
                self.add_template(obj)
                acted = True

            elif isinstance(obj, TemplateCall):

                templ = self._templates.get(call.typename)
                if not templ:
                    # defer for another pass
                    deferals.append(obj)

                else:
                    # attempt to expand the call. If there are existing
                    # deferals, then the expansion will just be inlined
                    # into the deferals. If not, then the expansion will
                    # be added
                    acted = acted or self._expand(
                        self.to_objects(templ.render_call(obj)),
                        deferals)

            else:
                raise ValueError(f"Unknown object type during expand {obj}")

        return acted


# The end.
