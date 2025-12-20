"""
koji_habitude.koji

Helper functions for koji client operations.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: Pure Human


import logging
from typing import (
    TYPE_CHECKING, Any, Callable, Dict, List, Optional, TypeVar,
)

from koji import (
    ClientSession, MultiCallSession, VirtualCall, VirtualMethod,
    read_config,
)
from .intern import intern
from koji_cli.lib import activate_session


if TYPE_CHECKING:
    from .models import BaseKey


__all__ = (
    'session',
    'multicall',
)


logger = logging.getLogger(__name__)


ENABLE_INTERNING = True


class InterningClientSession(ClientSession):
    """
    A client session that may intern the results of API calls to conserve
    memory
    """

    def _callMethod(self, name, args, kwargs=None, retry=True):
        return intern(super()._callMethod(name, args, kwargs, retry))


def session(
        profile: str = 'koji',
        authenticate: bool = False) -> ClientSession:
    """
    Create a koji client session.
    """

    conf = read_config(profile)
    server = conf["server"]
    session: ClientSession
    if ENABLE_INTERNING:
        session = InterningClientSession(server, opts=conf)
    else:
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
    A VirtualCall that triggers a callback when the call is
    completed. Unlike a VirtualCallProcessor, which performs a
    transformation on the result lazily, a VirtualPromise triggers its
    callback when the parent PromiseMultiCallSession stores the result
    value or exception into it.
    """

    def __init__(self, method: str, args, kwargs):
        self._real_result: Any = None
        self._trigger: Optional[Callable[['VirtualPromise'], None]] = None
        super().__init__(method, args, kwargs)


    @property
    def _result(self):
        return self._real_result


    @_result.setter
    def _result(self, value: Any):
        value = intern(value) if ENABLE_INTERNING else value
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
        raise TypeError(
            "sessionmethod must be a VirtualMethod,"
            f" got {type(sessionmethod)}"
        )

    result = sessionmethod(*args, **kwargs)
    if isinstance(result, VirtualCall):
        return VirtualCallProcessor(post_process, result)
    else:
        return post_process(result)


def promise_call(
        intofn: Callable[['VirtualPromise'], Any],
        sessionmethod, *args, **kwargs) -> None:

    promise = sessionmethod(*args, **kwargs)
    if isinstance(promise, VirtualPromise):
        promise.into(intofn)
    else:
        raise TypeError(
            "sessionmethod must return a VirtualPromise,"
            f"got {type(promise)}"
        )


class PromiseMultiCallSession(MultiCallSession):

    def _callMethod(
            self,
            name: str,
            args,
            kwargs=None,
            retry=True) -> VirtualPromise:

        logger.debug(f"callMethod({name!r}, {args!r}, {kwargs!r})")
        if kwargs is None:
            kwargs = {}
        ret = VirtualPromise(name, args, kwargs)
        self._calls.append(ret)
        return ret


CallDict = Dict['BaseKey', List[VirtualCall]]


class ReportingMulticall(PromiseMultiCallSession):
    """
    A multicall that associates the results of the calls with an object key.
    """

    def __init__(
            self,
            session: ClientSession,
            strict: bool = False,
            batch: Optional[int] = 100,
            associations: Optional[CallDict] = None):

        super().__init__(session, strict=strict, batch=batch)

        if associations is None:
            associations = {}

        self._associations: Dict['BaseKey', List[VirtualCall]] = associations
        self._call_log: List[VirtualCall] = associations.setdefault(None, [])


    def _callMethod(
            self,
            name: str,
            args,
            kwargs=None,
            retry=True) -> VirtualPromise:

        result = super()._callMethod(
            name, args, kwargs=kwargs, retry=retry)  # type: ignore
        self._call_log.append(result)
        return result


    def associate(self, key: 'BaseKey'):
        self._call_log = self._associations.setdefault(key, [])


def multicall(
        session: ClientSession,
        batch: Optional[int] = 100) -> PromiseMultiCallSession:
    """
    Create a multicall session that will record the calls made to it
    into the call_log list.

    :param session: The koji session to create the multicall session from
    :param batch: The batch size for the multicall session
    """

    # note that we make the call log mandatory here.
    mc = PromiseMultiCallSession(session, batch=batch)
    vars(mc)['_currentuser'] = vars(session)['_currentuser']
    return mc


# The end.
