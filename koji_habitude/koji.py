"""
koji_habitude.koji

Helper functions for koji client operations.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: Pure Human


import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from koji import (ClientSession, MultiCallSession, VirtualCall, VirtualMethod,
                  read_config)
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


class VirtualPromise(VirtualCall):
    """
    A VirtualCall that triggers a callback when the call is completed. Unlike a
    VirtualCallProcessor, which performs a transformation on the result lazily,
    a VirtualPromise triggers its callback when the parent
    PromiseMultiCallSession stores the result value or exception into it.
    """

    def __init__(
            self,
            method: str,
            args,
            kwargs):

        self._real_result: Any = None
        self._trigger: Optional[Callable[['VirtualPromise'], None]] = None
        super().__init__(method, args, kwargs)


    @property
    def _result(self):
        return self._real_result


    @_result.setter
    def _result(self, value: Any):
        self._real_result = value
        if trigger_fn := self._trigger:
            self._trigger = None
            trigger_fn(self)


    def into(self, trigger: Callable[['VirtualPromise'], Any]):
        self._trigger = trigger


class VirtualCallProcessor(VirtualCall):
    """
    A VirtualCall that transforms the result lazily
    """

    def __init__(self, post_process, vcall: VirtualCall):
        self._vcall = vcall
        self._post_process = post_process
        self._result = None
        self._processed = False


    @property
    def result(self):
        if not self._processed:
            self._result = self._post_process(self._vcall.result)
            self._processed = True
        return self._result


def call_processor(post_process, sessionmethod, *args, **kwargs):
    """
    A call that transforms the results
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


class PromiseMultiCallSession(MultiCallSession):

    def _callMethod(self, name: str, *args, **kwargs) -> VirtualPromise:
        if kwargs is None:
            kwargs = {}
        ret = VirtualPromise(name, args, kwargs)
        self._calls.append(ret)
        return ret


class ReportingMulticall(PromiseMultiCallSession):
    """
    A multicall that reports the results of the calls.
    """

    def __init__(
            self,
            session: ClientSession,
            strict: bool = False,
            batch: Optional[bool] = None,
            associations: Optional[Dict['BaseKey', List[VirtualPromise]]] = None):

        super().__init__(session, strict=strict, batch=batch)

        if associations is None:
            associations = {}

        self._associations: Dict['BaseKey', List[VirtualPromise]] = associations
        self._call_log: List[VirtualPromise] = associations.setdefault(None, [])


    def _callMethod(self, name: str, *args, **kwargs) -> VirtualPromise:
        result = super()._callMethod(name, *args, **kwargs)  # type: ignore
        self._call_log.append(result)
        return result


    def associate(self, key: 'BaseKey'):
        self._call_log = self._associations.setdefault(key, [])


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
