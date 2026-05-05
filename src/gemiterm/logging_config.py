import logging
import sys


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=level,
        format=log_format,
        stream=sys.stderr,
        force=True,
    )

    from gemini_webapi import set_log_level

    set_log_level("DEBUG" if verbose else "WARNING")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
