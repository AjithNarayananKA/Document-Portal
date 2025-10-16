import logging
import os
from datetime import datetime
import structlog

# class CustomLogger:
#     def __init__(self,log_dir="logs"):

#         # Creating Log directory (Ensuring logs directory exits)
#         self.log_dir = os.path.join(os.getcwd(), log_dir)
#         os.makedirs(self.log_dir,exist_ok=True)

#         #Creating time-stamped log file name
#         log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
#         log_file_path =os.path.join(self.log_dir,log_file)

#         # Configuring logging
#         logging.basicConfig(
#             filename=log_file_path,
#             format="[ %(asctime)s ] %(levelname)s %(name)s (line: %(lineno)d) - %(message)s",
#             level=logging.INFO
#         )
#     def get_Logger(self, name =__file__): # to capture current file name (store log in current file)
#         return logging.getLogger(os.path.basename(name))

# class CustomLogger:
#     def __init__(self,log_dir="logs"):

#         self.log_dir = os.path.join(os.getcwd(),log_dir)
#         os.makedirs(self.log_dir,exist_ok=True)

#         log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
#         self.log_file_path = os.path.join(self.log_dir,log_file)

#     def get_Logger(self,name = __file__):
#         """
#         Returns logger instance with file + console handlers.
#         Default name is the current file name (without path)
#         """
#         logger_name = os.path.basename(name)
#         logger = logging.getLogger(logger_name)
#         logger.setLevel(logging.INFO)

#         # File formatter
#         file_formatter = logging.Formatter(
#             "[ %(asctime)s ] %(levelname)s %(name)s (line: %(lineno)d) - %(message)s"
#         )
#         console_formatter = logging.Formatter(
#             "[ %(levelname)s] %(message)s"
#         )

#         # To save log in file
#         file_handler = logging.FileHandler(self.log_file_path)
#         file_handler.setFormatter(file_formatter)

#         # To print log on terminal
#         console_handler = logging.StreamHandler()
#         console_handler.setFormatter(console_formatter)

#         # Avoid duplicate handlers if logger is reused
#         if not logger.handlers:
#             logger.addHandler(file_handler)
#             logger.addHandler(console_handler)
        
#         return logger
   
# if __name__=="__main__":
#     logger = CustomLogger()
#     logger = logger.get_Logger(__file__)
#     logger.info("Custom Logger Initialized...")


class CustomLogger:

    def __init__(self,log_dir = "logs"):
        self.log_dir = os.path.join(os.getcwd(),log_dir)
        os.makedirs(self.log_dir, exist_ok=True)

        log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
        self.log_file_path = os.path.join(self.log_dir,log_file)


    def get_Logger(self,name = __file__):

        logger_name = os.path.basename(name)
        # logger = logging.getLogger(logger_name)
        # logger.setLevel(logging.INFO)

        # Configuring logging for console + file (both JSON)
        file_formatter = logging.Formatter("%(message)s")
        console_formatter = logging.Formatter("%(message)s")

        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter) 

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)

        logging.basicConfig(
            level = logging.INFO,
            format = "%(message)s", # Structlog will handle JSON rendering
            handlers = [file_handler, console_handler]
        )

        # Configuring structlog for JSON structured logging
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt='iso', utc= True, key='timestamp'),
                structlog.processors.add_log_level,
                structlog.processors.EventRenamer(to='event'),
                structlog.processors.JSONRenderer()
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use = True
        )

        return structlog.get_logger(logger_name)
    
if __name__ == "__main__":

    logger = CustomLogger().get_Logger(__file__)
    logger.info("Uploaded a file", userid =123, filename ='file.pdf')
    logger.error("Error processing the file", error="File is missing", user_id=123)