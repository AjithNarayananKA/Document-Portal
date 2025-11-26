import os
import fitz
import uuid
from datetime import datetime
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException

class DocumentHandler:
    """
    Handles PDF saving and reading operations
    Automatically logs all actions and supports session-based organization.
    """
    def __init__(self,data_dir=None,session_id=None):
        try:
            self.log = CustomLogger().get_Logger(__name__)
            self.data_dir = data_dir or os.getenv(
                "DATA_STORAGE_PATH",
                os.path.join(os.getcwd(),'data','document_analysis')
            )
            self.session_id = session_id or f"session_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}_{uuid.uuid4().hex[:8]}"

            # Create Session directory for data versioning
            self.session_path = os.path.join(self.data_dir,self.session_id)
            os.makedirs(self.session_path,exist_ok=True)
            
            self.log.info("PDF Handler Initialized", session_id=self.session_id,session_path=self.session_path)
        except Exception as e:
            self.log.error(f"Error initializing Document Handler : {e}")
            raise DocumentPortalException("Error in Initializing PDF Handler", e)
    def save_pdf(self,uploaded_file):
        try:
            file_name = os.path.basename(uploaded_file.name)

            if not file_name.lower().endswith(".pdf"):
                raise DocumentPortalException("Invalid file type. Only PDFs are allowed")
            
            save_path = os.path.join(self.session_path,file_name)

            with open(save_path, "wb") as f:
                f.write(uploaded_file.get_buffer())

            self.log.info("PDF saved successfully",file_name=file_name,save_path=save_path,session_id=self.session_id)
            return save_path
        except Exception as e:
            self.log.error(f"Error Saving PDF : {e}")
            raise DocumentPortalException("Error Saving PDF", e)
        
    def read_pdf(self,pdf_path:str)->str:
        try:
            text_chunks = []
            with fitz.open(pdf_path) as doc:
                for page_num,page in enumerate(doc,start=1):
                    text_chunks.append(f"\n-- Page {page_num} --\n{page.get_text()}")
            text =  "\n".join(text_chunks)
            self.log.info("PDF Read Successfully",pdf_path=pdf_path,session_id=self.session_id,pages=len(text_chunks))
            return text
        except Exception as e:
            self.log.error(f"Error reading PDF : {e}")
            raise DocumentPortalException("Error reading PDF", e)
        

if __name__ =="__main__":
    from pathlib import Path
    from io import BytesIO

    pdf_path = r"D:\\Document-Portal\\data\document_analysis\\NIPS-2017-attention-is-all-you-need-Paper.pdf"

    class Dummyfile:
        def __init__(self,file_path):
            self.name = Path(file_path).name
            self._file_path = file_path
        def get_buffer(self):
            return open(self._file_path, "rb").read()
            
    dummy_pdf = Dummyfile(pdf_path)
    handler = DocumentHandler()

    try:
        saved_path=handler.save_pdf(dummy_pdf)
        print(saved_path)

        content = handler.read_pdf(saved_path)
        print("PDF Content:")
        print(content[:500])

    except Exception as e:
        print(f"Error : {e}")