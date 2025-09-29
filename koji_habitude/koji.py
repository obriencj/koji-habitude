"""
koji_habitude.koji

Helper functions for koji client operations.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: Pure Human


import logging
from typing import Dict, List, Optional, TYPE_CHECKING

from koji import (
    ClientSession,
    MultiCallSession,
    VirtualCall,
    VirtualMethod,
    read_config,
)
from koji_cli.lib import activate_session

if TYPE_CHECKING:
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
    session.logger = logger

    if authenticate:
        activate_session(session, conf)
        vars(session)['_currentuser'] = session.getLoggedInUser()
    else:
        vars(session)['_currentuser'] = None

    return session


class VirtualCallProcessor(VirtualCall):
    """
    A VirtualCall that reports the results of the calls.
    """
    def __init__(self, post_process, vcall: VirtualCall):
        self._vcall = vcall
        self._post_process = post_process
        self._result = []

    @property
    def result(self):
        logger.debug(f"VirtualCallProcessor.result: {self._result}")
        if self._result:
            return self._result[0]

        res = self._vcall.result
        res = self._post_process(res)
        self._result.append(res)
        return res


def call_processor(post_process, sessionmethod, *args, **kwargs):
    """
    A multicall that reports the results of the calls.
    """
    if not isinstance(sessionmethod, VirtualMethod):
        raise TypeError(f"sessionmethod must be a VirtualMethod, got {type(sessionmethod)}")

    result = sessionmethod(*args, **kwargs)
    if isinstance(result, VirtualCall):
        logger.debug(f"VirtualCall: {result}")
        return VirtualCallProcessor(post_process, result)
    else:
        logger.debug(f"normal value: {result}")
        return post_process(result)


class ReportingMulticall(MultiCallSession):
    """
    A multicall that reports the results of the calls.
    """

    def __init__(
        self,
        session: ClientSession,
        strict: bool = False,
        batch: bool | None = None,
        associations: Optional[Dict['BaseKey', List[VirtualCall]]] = None,
        call_log: Optional[List[VirtualCall]] = None):

        super().__init__(session, strict=strict, batch=batch)

        if associations is None:
            associations = {}

        if call_log is None:
            call_log = []

        self._associations: Optional[Dict['BaseKey', List[VirtualCall]]] = associations
        self._call_log: Optional[List[VirtualCall]] = call_log


    def _callMethod(self, name: str, *args, **kwargs):
        result = super()._callMethod(name, *args, **kwargs)
        self._call_log.append(result)
        return result


    def associate(self, key: 'BaseKey'):
        log = self._associations.setdefault(key, [])
        self._call_log = log


def multicall(
    session: ClientSession,
    associations: Optional[Dict['BaseKey', List[VirtualCall]]] = None) -> ReportingMulticall:

    """
    Create a multicall session that will record the calls made to it
    into the call_log list.

    Args:
        session: The koji session to create the multicall session from
        associations: Dict of BaseKey to list of VirtualCall objects
    """

    # note that we make the call log mandatory here.
    mc = ReportingMulticall(session, associations=associations)
    vars(mc)['_currentuser'] = vars(session)['_currentuser']
    return mc


# The end.
