import logging
from langchain_logger.callback import ChainOfThoughtCallbackHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
        logfile="run.log",
        level=logging.INFO,
        console_output=True
    ):
    """
    Sets up logging with a rotating file handler.
    """
    logger = logging.getLogger() # root logger
    logger.setLevel(logging.INFO)

    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    Path(logfile).parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        logfile,
        maxBytes=5_000_000,  # 5MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.info("# ==================== Logging Setup ===================== #")
    logger.info(f"Log file: {logfile}")
    logger.info(f"Console output: {console_output}")
    logger.info("# ======================================================== #")