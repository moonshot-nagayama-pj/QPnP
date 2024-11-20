import sys
import threading
from types import TracebackType
from typing import Any

import structlog

from pnpq.events import Event
from tests.logs import setup_log

setup_log("hardware_tests")
log = structlog.get_logger()


def excepthook(
    exception_type: type[BaseException],
    e: BaseException,
    traceback: TracebackType | None,
) -> Any:
    log.error(event=Event.UNCAUGHT_EXCEPTION, exc_info=e)
    return sys.__excepthook__(exception_type, e, traceback)


sys.excepthook = excepthook


original_threading_excepthook = threading.excepthook


def threading_excepthook(args: Any) -> Any:
    log.error(event=Event.UNCAUGHT_EXCEPTION, exc_info=args.exc_value)
    return original_threading_excepthook(args)


threading.excepthook = threading_excepthook
