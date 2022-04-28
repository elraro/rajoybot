import logging

DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class LoggerFactory:

    def __init__(self, name):
        # create logger with name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(DEFAULT_LOG_LEVEL)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(DEFAULT_LOG_LEVEL)
        # create formatter and add it to the handlers
        ch.setFormatter(DEFAULT_FORMATTER)
        # add the handlers to the logger
        self.logger.addHandler(ch)

    def get_numeric_log_level(self, verbosity):
        numeric_level = getattr(logging, verbosity.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % verbosity)
        return numeric_level

    def set_log_level(self, verbosity):
        numeric_level = self.get_numeric_log_level(verbosity)
        for c_logger in self.logger.handlers:
            c_logger.setLevel(numeric_level)

    def get_logger(self):
        return self.logger

    def add_file_handler(self, file_path, log_level=DEFAULT_LOG_LEVEL, formatter=DEFAULT_FORMATTER):
        fh = logging.FileHandler(file_path)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
