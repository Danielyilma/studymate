from django.conf import settings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAI
import pickle

class BaseClient:
    api_key = settings.GOOGLE_API_KEY
    model = 'gemini-1.5-pro-latest'
    llm = GoogleGenerativeAI(model=model, google_api_key=api_key, verbose=True)

    def extract(self, file_path):
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600, chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)
        return texts
    

    def store_embeddings(self, docs, embeddings, sotre_name, path):
        vectorStore = FAISS.from_documents(docs, embeddings)

        with open(f"{path}/faiss_{sotre_name}.pkl", "wb") as f:
            pickle.dump(vectorStore, f)


    def load_embeddings(self, sotre_name, path):

        with open(f"{path}/faiss_{sotre_name}.pkl", "rb") as f:
            vectorStore = pickle.load()
        
        return vectorStore