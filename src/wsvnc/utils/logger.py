"""Basic logger."""

import logging


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
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger
