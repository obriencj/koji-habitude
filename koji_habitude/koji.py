"""
koji_habitude.koji

Helper functions for koji client operations.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: Pure Human


from typing import List, Optional, Dict
import logging

from koji import ClientSession, MultiCallSession, VirtualCall, read_config
from koji_cli.lib import activate_session

from .models import BaseKey


__all__ = (
    'session',
    'multicall',
)


logger = logging.getLogger(__name__)


def session(profile: str = 'koji', authenticate: bool = False) -> ClientSession:
    """
    Create a koji client session.
    """

    conf = read_config(profile)
    server = conf["server"]
    session = ClientSession(server, opts=conf)
    if authenticate:
        activate_session(session)
        vars(session)['_currentuser'] = session.getLoggedInUser()
    return session


class ReportingMulticall(MultiCallSession):
    """
    A multicall that reports the results of the calls.
    """

    def __init__(
        self,
        session: ClientSession,
        strict: bool = False,
        batch: bool | None = None,
        associations: Optional[Dict[BaseKey, List[VirtualCall]]] = None,
        call_log: Optional[List[VirtualCall]] = None):

        super().__init__(session, strict=strict, batch=batch)

        if associations is None:
            associations = {}

        if call_log is None:
            call_log = []

        self._associations: Optional[Dict[BaseKey, List[VirtualCall]]] = associations
        self._call_log: Optional[List[VirtualCall]] = call_log


    def _callMethod(self, name: str, *args, **kwargs):
        result = super()._callMethod(name, *args, **kwargs)
        self._call_log.append(result)
        return result


    def associate(self, key: BaseKey):
        log = self._associations.setdefault(key, [])
        self._call_log = log


def multicall(
    session: ClientSession,
    associations: Optional[Dict[BaseKey, List[VirtualCall]]] = None) -> ReportingMulticall:

    """
    Create a multicall session that will record the calls made to it
    into the call_log list.

    Args:
        session: The koji session to create the multicall session from
        associations: Dict of BaseKey to list of VirtualCall objects

    Usage:
    ```python
    call_log = []

    with multicall(session, call_log=call_log) as mc:
        # perform method calls againt the mc context, which will
        # each return a VirtualResult object that acts as a
        # promise for the eventual result of the call
        ...

    for call in call_log:
        print(call)  # each call is a VirtualCall object
    ```
    """

    # note that we make the call log mandatory here.
    mc = ReportingMulticall(session, associations=associations)
    vars(mc)['_currentuser'] = vars(session)['_currentuser']
    return mc


# The end.
