import os
import sys
from utils.model_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
from model.models import *
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser
from prompt.prompt_library import *

class DocumentAnalyzer:
    """
    Analyze document using a pre-trained model.
    Automatically logs all actions and support session-based organization.
    """
    def __init__(self):
        self.log = CustomLogger().get_Logger(__name__)

        try:
            self.model_loader = ModelLoader()
            self.llm = self.model_loader.load_llm()

            self.parser = JsonOutputParser(pydantic_object= Metadata)
            self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser,llm=self.llm)

            self.prompt = prompt

            self.log.info("Document Analyzer successfully Initialized.")

        except Exception as e:
            self.log.error(f'Error Initializing Document Analyzer:{e}')
            raise DocumentPortalException("Error in Document Analyzer Initialization",e)

    def analyze_document(self, document:str)-> dict:
        """Extract the text from the document and extract structured metadata and summary"""
        
        chain = self.prompt | self.llm | self.fixing_parser

        self.log.info("Rag chain is successfully initialized.")

        response = chain.invoke({
            "format_instructions":self.parser.get_format_instructions(),
            "document_text": document
            })
        
        self.log.info('Metadata extraction successful', keys=list(response.keys()))
        return response
