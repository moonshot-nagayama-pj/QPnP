import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import structlog


def find_project_dir(path: Path) -> Path:
    if path.is_dir():
        for contained_path in path.iterdir():
            if contained_path.name == "pyproject.toml":
                return path
    return find_project_dir(path.parent)


def setup_log(log_file_name: str) -> None:
    target_dir = find_project_dir(Path(__file__).resolve()).joinpath("target")
    target_dir.mkdir(exist_ok=True)

    structlog.configure(
        processors=[
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Rotate the log file every 100MB and keep 3 backups
    handler = RotatingFileHandler(
        target_dir.joinpath(f"{log_file_name}.log"),
        maxBytes=100 * 1024 * 1024,
        backupCount=3,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.dict_tracebacks,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ]
    )
    handler.setFormatter(formatter)

    logging.basicConfig(handlers=[handler], level=logging.DEBUG)
