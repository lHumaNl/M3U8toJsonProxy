import logging


class LoggerModel:
    __LOGGER_STR_FORMAT = '[%(asctime)s] %(levelname)s | ' \
                          'module: %(module)s | ' \
                          'funcName: %(funcName)s | ' \
                          'message: %(message)s'

    __LOGGER_DATE_FORMAT = '%d-%m-%Y %H:%M:%S'
    __LOG_FORMATTER = logging.Formatter(__LOGGER_STR_FORMAT, datefmt=__LOGGER_DATE_FORMAT)

    __DEBUG_LEVEL = logging.DEBUG
    __ERROR_LEVEL = logging.ERROR
    __CRITICAL_LEVEL = logging.CRITICAL
    __INFO_LEVEL = logging.INFO

    @staticmethod
    def init_logger():
        root_logger = logging.getLogger()
        root_logger.setLevel(LoggerModel.__DEBUG_LEVEL)

        console_handler = logging.StreamHandler()

        LoggerModel.__add_logger_handler(console_handler, LoggerModel.__INFO_LEVEL, root_logger)

    @staticmethod
    def __add_logger_handler(handler, level, root_logger):
        logger_handler = handler
        logger_handler.setFormatter(LoggerModel.__LOG_FORMATTER)
        logger_handler.setLevel(level)
        root_logger.addHandler(logger_handler)
