"""
koji_habitude.intern

String interning utility for YAML documents and Koji objects

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 4.5 Sonnet via Cursor
"""

# Vibe-Coding State: Pure Human


from typing import Any, TypeVar


def setup_interning():
    # This may seem silly, but in cases of Very Large Product configurations,
    # which I will not name here, the YAML export can be over 60MB. In those
    # cases, this series of optimizations can shave off 1 second of load time,
    # and save 150MB of resident memory.
    #
    # For smaller datasets (eg. a 3MB file), the performance is slower by
    # about 0.05 sec, but can still save around 4MB
    #
    # See the tools/profile_yaml_interning.py script for more details.

    from sys import intern as intern_str
    is_str = str.__instancecheck__
    is_dict = dict.__instancecheck__
    is_list = list.__instancecheck__
    enum = enumerate

    T = TypeVar('T', bound=Any)


    def intern_collection(doc: T) -> T:
        if is_dict(doc):
            for key, value in doc.items():
                if is_str(value):
                    doc[key] = intern_str(value)
                else:
                    doc[key] = intern_collection(value)
        elif is_list(doc):
            for i, value in enum(doc):
                if is_str(value):
                    doc[i] = intern_str(value)
                else:
                    doc[i] = intern_collection(value)
        return doc


    def intern_any(doc: T) -> T:
        if is_str(doc):
            return intern_str(doc)  # type: ignore

        if is_dict(doc):
            for key, value in doc.items():
                if is_str(value):
                    doc[key] = intern_str(value)
                else:
                    doc[key] = intern_collection(value)
        elif is_list(doc):
            for i, value in enum(doc):
                if is_str(value):
                    doc[i] = intern_str(value)
                else:
                    doc[i] = intern_collection(value)
        return doc


    return intern_any


intern = setup_interning()


# The end.
