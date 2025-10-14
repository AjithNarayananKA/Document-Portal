import logging
import os
from datetime import datetime

class CustomLogger:
    def __init__(self,log_dir="logs"):

        # Creating Log directory (Ensuring logs directory exits)
        self.log_dir = os.path.join(os.getcwd(), log_dir)
        os.makedirs(self.log_dir,exist_ok=True)

        #Creating time-stamped log file name
        log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
        log_file_path =os.path.join(self.log_dir,log_file)

        # Configuring logging
        logging.basicConfig(
            filename=log_file_path,
            format="[ %(asctime)s ] %(levelname)s %(name)s (line: %(lineno)d) - %(message)s",
            level=logging.INFO
        )
    def get_Logger(self, name =__file__): # to capture current file name (store log in current file)
        return logging.getLogger(os.path.basename(name))
    
if __name__=="__main__":
    logger = CustomLogger()
    logger = logger.get_Logger(__file__)
    logger.info("Custom Logger Initialized...")

