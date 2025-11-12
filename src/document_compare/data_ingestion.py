import sys
import uuid
from pathlib import Path
import fitz
from datetime import datetime, timezone
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException

class DocumentIngestion:
    """
    Handles saving, reading, and combining of PDFs for comparison with session-based versioning.
    """
    def __init__(self,base_dir : str ="data/document_compare", session_id=None):
        self.log = CustomLogger().get_Logger(__name__)
        self.base_dir = Path(base_dir)
        self.session_id = session_id or f"{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}_{uuid.uuid4().hex[:8]}"
        self.session_path = self.base_dir / self.session_id
        self.session_path.mkdir(parents=True, exist_ok=True)

        self.log.info("Document Ingestion Initialized",session_path = str(self.session_path))

    # def delete_existing_files(self):
    #     """Deletes existing files at the specified paths."""
    #     try:
    #         if self.base_dir.exists() and self.base_dir.is_dir():
    #             for file in self.base_dir.iterdir():
    #                 if file.is_file():
    #                     file.unlink()
    #                     self.log.info("File deleted", path=str(file))
    #             self.log.info("Directory cleaned", path =str(self.base_dir))
    #     except Exception as e:
    #         self.log.error(f"Error deleting existing file: {e}")
    #         raise DocumentPortalException("An error occurred while deleting an existing file",sys)

    def save_uploaded_files(self,reference_file, actual_file):
        """Saves reference and actual PDF files to a session directory."""
        try:
            # self.delete_existing_files()

            ref_path = self.base_dir / reference_file.name
            act_path = self.base_dir / actual_file.name

            if not reference_file.name.lower().endswith(".pdf") or not actual_file.name.lower().endswith(".pdf"):
                raise ValueError("Only PDF files are allowed.")
            
            with open(ref_path, "wb") as f:
                f.write(reference_file.get_buffer())

            with open(act_path, "wb") as f:
                f.write(actual_file.get_buffer())
            self.log.info("Files saved", reference=str(ref_path), actual=str(act_path), session=self.session_id)
            return ref_path, act_path
        except Exception as e:
            self.log.error(f"Error saving uploaded files: {e}")
            raise DocumentPortalException("An error occurred while saving uploaded file.",sys)

    def read_pdf(self, pdf_path: Path)-> str:
        """
        Reads text content of a PDF page-by-page.
        """
        try:
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    raise ValueError(f"PDF is encrypted: {pdf_path.name}")
                text_chunks = []
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    if text.strip():
                        text_chunks.append(f"\n---Page {page_num + 1} ---\n{text}")
                    self.log.info("PDF read successfully", file = str(pdf_path), pages = len(text_chunks))
                    return "\n".join(text_chunks)
        except Exception as e:
            self.log.error(f"Error reading PDF: {e}")
            raise DocumentPortalException("An error occurred while reading the PDF",sys)
        
    def combine_documents(self) -> str:
        """
        Combine content of all PDFs in session folder into a single string
        """
        try:
            doc_parts = []

            for file in sorted(self.session_path.iterdir()):
                if file.is_file() and file.suffix.lower() == ".pdf":
                    content = self.read_pdf(file)
            
                doc_parts.append(f"Document:{file}\n {content}")

            combine_text = "\n\n".join(doc_parts)
            self.log.info("Document combined", count=len(doc_parts), session=self.session_id)
            return combine_text
        
        except Exception as e:
            self.log.error(f"Error combining documents : {e}")
            raise DocumentPortalException("An error occurred while combining documents", sys)
        
    def clean_old_sessions(self,keep_latest: int =3):
        """
        Optional method to delete older session folders, keeping only the latest N.
        """
        try:
            session_folders = sorted([file for file in self.base_dir.iterdir() if file.is_dir()],reverse=True)
            for folder in session_folders[keep_latest:]:
                for file in folder.iterdir():
                    file.unlink()
                folder.rmdir()
                self.log.info("Old session folder deleted", path =str(folder))

        except Exception as e:
            self.log.error("Error cleaning old sessions", error=str(e))
            raise DocumentPortalException("Error cleaning old sessions", sys)