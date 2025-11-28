from __future__ import annotations
import os
import sys
import json
import uuid
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Iterable

import fitz
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.vectorstores import FAISS


from utils.model_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException

from utils.file_io import _session_id, save_uploaded_files
from utils.document_ops import load_documents, concat_for_analysis, concat_for_comparison

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# FAISS Manager (load-or-create)
class FaissManager:
    def __init__(self, index_dir:str, model_loader: Optional[ModelLoader]=None):
        
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents = True, exist_ok= True)
        
        self.meta_path = self.index_dir / "ingested_meta.json"
        self._meta : Dict[str, Any] = {"rows": {}}
        
        if self.meta_path.exists():
            try:
                self._meta = json.loads(self.meta_path.read_text(encoding="utf-8")) or {"rows": {}}
            except Exception as e:
                self._meta = { "rows":{}}
                
        self.model_loader = model_loader or ModelLoader()
        self.embedding = self.model_loader.load_embedding()
        self.vector_store : Optional[FAISS] = None
        
    def _exists(self)-> bool:
        return (self.index_dir / "index.faiss").exists() and (self.index_dir / "index.pkl").exists()
    
    @staticmethod
    def _fingerprint(text: str, md: Dict[str, any])-> str:
        src = md.get("source") or md.get("file_path")
        row_id = md.get("row_id")
        
        if src is not None:
            return f"{src}::{'' if row_id is None else row_id}"
        return hashlib.sha256(text.encode(encoding="utf-8")).hexdigest()
    
    def _save_meta(self):
        self.meta_path.write_text(json.dumps(self._meta,ensure_ascii=True), encoding="utf-8")
    def add_documents(self,docs:List[Document]):
        if self.vector_store is None:
            raise RuntimeError("call load_or_create() before add_document")
        new_docs : List[Document] = []
        
        for d in docs:
            key = self._fingerprint(d.page_content, d.metadata or {})
            if key in self._meta["rows"]:
                continue
            self._meta["rows"][key] = True
            new_docs.append(d)
            
        if new_docs:
            self.vector_store.add_documents(new_docs)
            self.vector_store.save_local(str(self.index_dir))
            self._save_meta()
            return len(new_docs)
        
    def load_or_create(self):
        if self._exists():
            self.vector_store = FAISS.load_local(
                str(self.index_dir),
                embeddings= self.embedding,
                allow_dangerous_deserialization= True
            )
            return self.vector_store
class DocHandler:
    def __init__(self,data_dir: Optional[str]=None, session_id:Optional[str]=None):
        self.log = CustomLogger().get_Logger(__name__)
        self.data_dir = data_dir or os.getenv("DATA_DIRECTORY",os.path.join(os.getcwd(), "data", "document_analysis"))
        self.session_id = session_id or _session_id("session")
        self.session_dir = os.path.join(data_dir, session_id)
        os.makedirs(self.session_dir, exist_ok =True)
        self.log.info("DocHandler initialized",session_id=self.session_id, session_path =self.session_dir)
    def save_pdf(self, uploaded_file)->str:
        try:
            self.file_name = os.path.basename(uploaded_file)
            if not self.file_name.lower().endswith(".pdf"):
                raise ValueError("Invalid file type. Upload PDF file...")
            saved_path = os.path.join(self.session_dir, uploaded_file)
            with open(saved_path, "wb") as f:
                if hasattr(uploaded_file, "read"):
                    f.write(uploaded_file.read())
                else:
                    f.write(uploaded_file.get_buffer())
            self.log.info("PDF saved successfully", filename =self.file_name, saved_path = saved_path, session_id = self.session_id)
            return saved_path
        except Exception as e:
            self.log.error("Error saving PDF", error=str(e), session_id = self.session_id)
            raise DocumentPortalException(f"Failed to save PDF:{str(e)}", e) from e
    def read_pdf(self,pdf_path:str)->str:
        try:
            chunks=[]
            with fitz.open(pdf_path) as f:
                for page_num in range(f.page_count):
                    page = f.load_page(page_num)
                    text = page.get_text()
                    chunks.append(f"\n--Page {page_num+1}--\n{text}")
            self.log.info("PDF read successfully.", pdf_path =pdf_path, session_id =self.session_id)
            return "\n".join(chunks)
        except Exception as e:
            self.log.error("Error reading PDF", error= str(e), session_id =self.session_id)
            raise DocumentPortalException(f"Failed to read PDF: {str(e)}", e1) from e
class DocumentComparator:
    def __init__(self):
        pass
    def save_uploaded_files(self):
        pass
    def read_pdf(self):
        pass
    def combine_documents(self):
        pass
    def clean_old_sessions(self):
        pass
class ChatIngestor:
    def __init__(self):
        pass
    def _resolve_dir(self):
        pass
    def _split(self):
        pass
    def build_retriever(self):
        pass