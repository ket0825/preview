import logging
import settings

LOGGER_NAME = 'honeybee'

class Logger:
    """
    Should get instance only get_instance. \n
    --------------------------------------- \n
    USE CASE: \n
    log = Loggger.get_instance() \n
    log.info("Message what you want to record.") \n 
    """
    _instance = None

    def __init__(self, log_level=logging.INFO) -> None:
        self.logger = logging.getLogger(LOGGER_NAME) # named logger 설정.
        self.logger.setLevel(log_level)
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s: %(funcName)s \n%(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p'
            )
        stream_handler = logging.StreamHandler() #그냥 handler는 ABC임.
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

    def get_logger(self):
        return self.logger
        
    # singleton approach.
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls(log_level=settings.log_level).get_logger()
        return cls._instance

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.info(msg)
    
    def error(self, msg):
        self.logger.error(msg)
    
    def critical(self, msg):
        self.logger.critical(msg)



       