import uuid
from pathlib import Path
import sys
from datetime import datetime, timezone
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
from utils.model_loader import ModelLoader

class DocumentIngestor:

    def __init__(self, data_dir: str ="data/multi_doc_chat", faiss_dir: str ="faiss_index", session_id : str | None = None):
        
        self.SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
        
        try:
            self.log = CustomLogger().get_Logger(__name__)

            self.data_dir = Path(data_dir)
            self.faiss_dir = Path(faiss_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.faiss_dir.mkdir(parents=True,exist_ok=True)

            self.session_id = session_id or f"{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}_{uuid.uuid4().hex[:8]}"
            self.session_data_dir = self.data_dir / self.session_id
            self.session_faiss_dir = self.faiss_dir / self.session_id
            self.session_data_dir.mkdir(parents=True, exist_ok=True)
            self.session_faiss_dir.mkdir(parents=True, exist_ok=True)

            self.model_loader = ModelLoader()

            self.log.info(
                "DocumentIngestor initialized successfully",
                data_path = str(self.data_dir),
                faiss_path = str(self.faiss_dir),
                session_id = self.session_id,
                session_data_path = str(self.session_data_dir),
                session_faiss_path = str(self.session_faiss_dir)
            )
        except Exception as e:
            self.log.error("Failed to initialize DocumentIngestor", error=str(e))
            raise DocumentPortalException("Initialization error in DocumentIngestor", sys)

    def ingest_files(self,uploaded_files):
        
        try:
            documents = []

            for file in uploaded_files:
                file_ext = Path(file.name).suffix.lower()
                if file_ext not in self.SUPPORTED_EXTENSIONS:
                    self.log.warning("Unsupported file_ext, Skipped the file", ext = file_ext)
                    continue
                unique_name = f"{uuid.uuid4().hex[:8]}{file_ext}"
                file_path = self.session_data_dir / unique_name

                with open(file_path, "wb") as f:
                    f.write(file.read())
                self.log.info("File saved for ingestion.", filename = file.name, saved_as = str(file_path), session_id = self.session_id)

                if file_ext == ".pdf":
                    loader = PyPDFLoader(file_path=str(file_path))
                elif file_ext == ".docx":
                    loader = Docx2txtLoader(file_path=str(file_path))
                elif file_ext == ".txt":
                    loader = TextLoader(file_path=str(file_path), encoding = "utf-8")
                else:
                    self.log.warning("Unsupported file type encountered.", extension = file_ext, uploaded_file = file.name)
                    continue
                docs = loader.load()
                documents.extend(docs)

            if not documents:
                raise DocumentPortalException("No valid documents loaded", sys)
            self.log.info("All documents loaded", total_docs =len(documents),session_id = self.session_id)
            return self._create_retriever(documents)
        except  Exception as e:
            self.log.error("Failed to ingest files", error = str(e))
            raise DocumentPortalException("Ingestion Error in DocumentIngestor", sys)
    def _create_retriever(self, documents):
        
        try:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 300)
            chunks = text_splitter.split_documents(documents)
            self.log.info("Documents splitted into chunks", total_chunks =len(chunks), session_id = self.session_id)

            embedding = self.model_loader.load_embedding()
            vector_store = FAISS.from_documents(documents= chunks, embedding=embedding)

            vector_store.save_local(folder_path=str(self.session_faiss_dir))
            self.log.info("FAISS index saved to disk", path =str(self.session_faiss_dir), session_id = self.session_id)

            retriever = vector_store.as_retriever(search_type = "similarity", search_kwargs ={"k": 5})
            self.log.info("FAISS retriever created and ready to use", session_id = self.session_id)

            return retriever
        
        except Exception as e:
            self.log.error("Failed to create retriever", error = str(e))
            raise DocumentPortalException("Retrieval error in DocumetIngestor", sys)
