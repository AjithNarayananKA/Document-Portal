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
        
    def load_or_create(self, text:Optional[List[str]]=None, metadata:Optional[List[Dict]]=None):
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
            raise DocumentPortalException(f"Failed to read PDF: {str(e)}", e) from e
class DocumentComparator:
    def __init__(self, base_dir :str = "data/document_compare", session_id : Optional[str] = None ):
        self.log = CustomLogger().get_Logger(__name__)
        self.base_dir = Path(base_dir)
        
        self.session_id = session_id or _session_id()
        self.session_dir = self.base_dir / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.log.info("DocumentComparator initialized successfully.", session_id =str( self.session_id))
        
    def save_uploaded_files(self,ref_file:str, act_file:str):
        try:
            ref = os.path.basename(ref_file)
            act = os.path.basename(act_file)
            ref_path = os.path.join(self.session_dir, ref)
            act_path = os.path.join(self.session_dir, act)
            for fileobject , save_path in ((ref_file, ref_path), (act_file,act_path)):
                if not fileobject.lower().endswith(".pdf"):
                    raise ValueError("Invalid format. Upload PDF file.")
                with open(save_path, "wb") as f:
                    if hasattr(fileobject, "read"):
                        f.write(fileobject.read())
                    else:
                        f.write(fileobject.get_buffer())
            self.log.info("PDF files saved successfully", reference = str(ref_path), actual = str(act_path), session_id = self.session_id)
            return ref_path, act_path
        except Exception as e:
            self.log.error("Error saving PDF files.", error=str(e), session_id = self.session_id)
            raise DocumentPortalException(f"Failed to save PDF files: {str(e)}", e) from e
    def read_pdf(self, pdf_path: str):
        try:
            with fitz.open(pdf_path) as f:
                if f.is_encrypted():
                    raise ValueError(f"PDF is encrypted:{pdf_path.name}")
                chunks = []
                for page_num in range(f.page_count):
                    page = f.load_page(page_num)
                    text = page.get_text()
                    if text.strip():
                        chunks.append(f"\n--Page{page_num+1}--\n{text}")
                    
            self.log.info("Successfully read PDF", pdf_path = str(pdf_path), session_id = self.session_id)
            return "\n".join(chunks)
        
        except Exception as e:
            self.log.error("Error reading PDF files.", error=str(e), session_id = self.session_id)
            raise DocumentPortalException(f"Failed to read PDF files: {str(e)}", e) from e
    def combine_documents(self)-> str:
        try:
            docs_part =[]
            for fileobject in sorted(self.session_dir.iterdir()):
                if fileobject.is_file() and fileobject.suffix.lower() == ".pdf":
                    content = self.read_pdf(fileobject)
                    docs_part.append(f"Document:{fileobject.name}\n{content}")
            self.log.info("Successfully combined documents", page_count = len(docs_part) , session_id = self.session_id)
            return "\n".join(docs_part)
        except Exception as e:
            self.log.error("Error combining PDF files.", error=str(e), session_id = self.session_id)
            raise DocumentPortalException(f"Failed to combine PDF files: {str(e)}", e) from e
    def clean_old_sessions(self, keep_latest: int = 3):
        try:
            sessions = sorted([f for f in self.base_dir.iterdir() if f.is_dir()], reverse=True)
            for folder in sessions[keep_latest]:
                shutil.rmtree(folder, ignore_errors=True)
                self.log.info("Old session folder deleted", path =str(folder))
        except Exception as e:
            self.log.error("Error in cleaning old sessions.", error=str(e), session_id = self.session_id)
            raise DocumentPortalException(f"Failed to clean old sessions: {str(e)}", e) from e
class ChatIngestor:
    def __init__(self,
        temp_base:str ='data',
        faiss_base:str = "faiss_index",
        use_session_dir : bool = True,
        session_id : Optional[str] = None
        ):
        try:
            self.log = CustomLogger().get_Logger(__name__)
            self.model_loader = ModelLoader()
            
            
            self.temp_base = Path(temp_base); self.temp_base.mkdir(parents=True, exist_ok=True)
            self.faiss_base = Path(faiss_base); self.faiss_base.mkdir(parents=True, exist_ok=True)
            
            self.use_session = use_session_dir
            self.session_id = session_id or _session_id()
            
            self.temp_dir = self._resolve_dir(self.temp_base)
            self.faiss_dir  = self._resolve_dir(self.faiss_base) 
            
            self.log.info(
                "ChatIngestor initialized.",
                session_id = str(self.session_id),
                temp_dir = str(self.temp_dir),
                faiss_dir = str(self.faiss_dir),
                sessionized = self.use_session
            )
        except Exception as e:
            self.log.error("Error initializing ChatIngestor",error=str(e))
            raise DocumentPortalException(f"Failed to initialize ChatIngestor:{str(e)}", e) from e
    def _resolve_dir(self, base:Path):
        if self.use_session :
            d = base / self.session_id
            d.mkdir(parents=True, exist_ok=True)
            return d
        return base
    def _split(self, docs: List[Document], chunk_size = 1000, chunk_overlap = 200)-> List[Document]:
        splitter = RecursiveCharacterTextSplitter(chunk_size = chunk_size, chunk_overlap = chunk_overlap)
        chunks = splitter.split_documents(docs)
        self.log.info("Document splitted", chunks = len(chunks), chunk_size = chunk_size, overlap = chunk_overlap)
        return chunks
    def build_retriever(self,
        upload_files: Iterable,
        *,
        chunk_size: int = 1000,
        chunk_overlap:int = 200,
        k: int = 3   
        ):
        try:
            paths = save_uploaded_files(upload_files, self.temp_dir)
            docs = load_documents(paths)
            if not docs:
                raise ValueError("No valid documents loaded")
            chunks = self._split(docs, chunk_size= chunk_size, chunk_overlap= chunk_overlap)
            fm = FaissManager(self.faiss_dir,self.model_loader)
            
            text = [c.page_content for c in chunks]
            metadata = [c.metadata for c in chunks]
            try:
                vs = fm.load_or_create(text = text, metadata = metadata)
            except Exception:
                vs = fm.load_or_create(text = text, metadata = metadata)
            added = fm.add_documents(chunks)
            self.log.info("FAISS index updated", added = added, index = str(self.faiss_dir))
            return vs.as_retriever(search_type = 'similarity', search_kwargs = {"k":k})
        
        except Exception as e:
            self.log.error("Error building retriever", error = str(e))
            raise DocumentPortalException(f" Failed to build retriever: {str(e)}", e) from e