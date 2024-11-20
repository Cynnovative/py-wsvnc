"""Basic logger."""

import logging
import os


def get_logger(name: str) -> logging.Logger:
    """Get a logger.

    Parameters
    ----------
    name : str
        Name of the logger, typically __name__ is provided here

    Returns
    -------
    logging.Logger
        A logger
    """
    logger = logging.getLogger(name)
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        level=os.environ.get("LOGLEVEL", "INFO"),
    )
    return logger
