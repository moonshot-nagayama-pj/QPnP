from pathlib import Path

from logging.handlers import RotatingFileHandler
from structlog.processors import JSONRenderer
from structlog.stdlib import ProcessorFormatter

import logging
import structlog
import sys

def find_project_dir(path: Path) -> Path:
    if path.is_dir():
        for contained_path in path.iterdir():
            if contained_path.name == "pyproject.toml":
                return path
    return find_project_dir(path.parent)


target_dir = find_project_dir(Path(__file__).resolve()).joinpath("target")
target_dir.mkdir(exist_ok=True)

def setup_log(log_file_name):
    target_dir = find_project_dir(Path(__file__).resolve()).joinpath("target")
    target_dir.mkdir(exist_ok=True)

    # Rotate the log file every 3MB
    # handler = RotatingFileHandler(target_dir.joinpath(f"{log_file_name}.log"), maxBytes=3 * 1024 * 1024, backupCount=1)
    handler = RotatingFileHandler(target_dir.joinpath(f"{log_file_name}.log"), maxBytes=1 * 1024, backupCount=3)
    handler.setFormatter(logging.Formatter('%(message)s')) # Log only the message
    logging.basicConfig(handlers=[handler], level=logging.DEBUG)

    # Configure structlog and add a wrapper class to the logger
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.dict_tracebacks,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
    )
