import logging

def setup_logger(name=None, level=logging.INFO):
    """
    Set up a logger that can be used across modules.
    
    Args:
        name (str): Logger name. Use `__name__` for module-specific loggers.
        level (int): Logging level (e.g., logging.INFO, logging.DEBUG).
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding multiple handlers if logger is reused
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
