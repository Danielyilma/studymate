from io import BytesIO
from pypdf import PdfReader
from langchain.docstore.document import Document


def load_pdf_to_documents_from_bytes(file_bytes):
    file_stream = BytesIO(file_bytes)
    reader = PdfReader(file_stream)
    
    documents = []
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        documents.append(Document(page_content=text, metadata={"page": i}))
        
    return documents
