import logging

_log_format = f"%(asctime)s - [%(levelname)s] : %(name)s - (%(filename)s.%(funcName)s:%(lineno)d) - %(message)s"


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
