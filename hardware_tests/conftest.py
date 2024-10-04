import structlog
import sys
import threading

from pathlib import Path
from pnpq.events import Event
from types import TracebackType
from typing import Any


def find_project_dir(path: Path) -> Path:
    if path.is_dir():
        for contained_path in path.iterdir():
            if contained_path.name == "pyproject.toml":
                return path
    return find_project_dir(path.parent)


target_dir = find_project_dir(Path(__file__).resolve()).joinpath("target")
target_dir.mkdir(exist_ok=True)

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.dict_tracebacks,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.WriteLoggerFactory(
        file=target_dir.joinpath("hardware_tests.log").open("a")
    ),
)

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
