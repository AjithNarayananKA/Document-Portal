import sys
import traceback
from logger.custom_logger import CustomLogger

logger = CustomLogger().get_Logger(__file__)

class DocumentPortalException(Exception):
    def __init__(self,error_message,error_details:sys):
        _,_,exc_tb = error_details.exc_info()
        self.filename = exc_tb.tb_frame.f_code.co_filename
        self.lineno = exc_tb.tb_lineno
        self.error_message = str(error_message)
        self.traceback_str = ''.join(traceback.format_exception(*error_details.exc_info()))

    def __str__(self):
        return f""" Error in [{self.filename}] at line [{self.lineno}]
        Message : {self.error_message}
        Traceback : {self.traceback_str}
        """

if __name__ == "__main__":
    try:
        a= 1/0
        print(a)
    except Exception as e:
        app_exc = DocumentPortalException(e,sys)
        logger.error(app_exc)
        raise app_exc



