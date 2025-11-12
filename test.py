# test.py code for document_analysis

# from pathlib import Path
# from src.document_analyzer.data_ingestion import DocumentHandler
# from src.document_analyzer.data_analysis import DocumentAnalyzer

# pdf_path =r"D:\\Document-Portal\\data\document_analysis\\NIPS-2017-attention-is-all-you-need-Paper.pdf"

# class Dummyfile:
#     def __init__(self,file_path):
#         self.name = Path(file_path).name
#         self._file_path = file_path
        
#     def get_buffer (self):
#         return open(self._file_path, "rb").read() 
    
# def main():
#     try:
#     # ---------- STEP 1: DATA INGESTION ----------
#         print("Starting PDF ingestion...")
#         doc_file = Dummyfile(pdf_path)

#         doc_handler = DocumentHandler(session_id='test_document_analysis')
        
#         saved_path = doc_handler.save_pdf(doc_file)
#         print(f"PDF saved at: {saved_path}")
        
#         text_content = doc_handler.read_pdf(saved_path)
#         print(f"Extracted text length: {len(text_content)} chars\n")

#         # ---------- STEP 2: DATA ANALYSIS ----------
#         print("Starting metadata analysis...")
#         pdf_analyzer = DocumentAnalyzer()

#         analysis_result = pdf_analyzer.analyze_document(text_content)
        

#         # ---------- STEP 3: DISPLAY RESULTS ----------
#         print("\n=== METADATA ANALYSIS RESULT ===")
#         for key, value in analysis_result.items():
#             print(f"{key}: {value}")

#     except Exception as e:
#         print(f"Test failed: {e}")

# if __name__ == "__main__":
#     main()

# test.py code for document_comparison

import io
from pathlib import Path
from src.document_compare.data_ingestion import DocumentIngestion
from src.document_compare.document_comparator import DocumentCompareLM


def load_fake_uploaded_file(filepath:Path):
    return io.BytesIO(filepath.read_bytes())

def test_document_compare():
    act_path = Path("D:\\Document-Portal\\data\\document_compare\\report-1.pdf")
    ref_path = Path("D:\\Document-Portal\\data\\document_compare\\report-2.pdf")

    class FakeUpload:

        def __init__(self,file_path:Path):
            self.name = file_path.name
            self._buffer = file_path.read_bytes()

        def get_buffer(self):
            return self._buffer
        
    document_ingest = DocumentIngestion()
    ref_upload = FakeUpload(ref_path)
    act_upload = FakeUpload(act_path)

    ref_file, act_file = document_ingest.save_uploaded_files(ref_upload,act_upload)
    combined_text = document_ingest.combine_documents()
    document_ingest.clean_old_sessions(keep_latest=3)

    print("\n Combined text preview(First 1000 chars):\n")
    print(combined_text[:1000])

    llm_comparator = DocumentCompareLM()
    compare_df = llm_comparator.compare_document(combined_text)

    print("\n=== COMPARISON RESULT ===")
    print(compare_df.head())

if __name__ == "__main__":
    test_document_compare()