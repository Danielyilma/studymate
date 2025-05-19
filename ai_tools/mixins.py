from django.conf import settings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAI
import pickle
import json

class BaseClient:
    api_key = settings.GOOGLE_API_KEY
    model = 'gemini-2.0-flash'
    llm = GoogleGenerativeAI(model=model, google_api_key=api_key, verbose=True)

    def extract(self, file_path):
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600, chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)
        return texts


    def parse_json_like_content(self, input_text):
        """
        Parse a JSON-like string that may contain code block markers or a `json` prefix.
        
        Args:
            input_text (str): The input text to parse.
            
        Returns:
            dict or list: Parsed JSON data as a Python object.
            
        Raises:
            ValueError: If the input is not valid JSON.
        """
        # Step 1: Remove code block markers if present
        if input_text.startswith("```"):
            input_text = input_text[3:].strip()

        if input_text.endswith("```"):
            input_text = input_text[:-3].strip()

        # Step 2: Remove the `json` prefix if present
        if input_text.startswith("json"):
            input_text = input_text[4:].strip()

        # Step 3: Parse the JSON content
        try:
            return json.loads(input_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON content: {e}")
    

    def store_embeddings(self, docs, embeddings, sotre_name, path):
        vectorStore = FAISS.from_documents(docs, embeddings)

        with open(f"{path}/faiss_{sotre_name}.pkl", "wb") as f:
            pickle.dump(vectorStore, f)


    def load_embeddings(self, sotre_name, path):

        with open(f"{path}/faiss_{sotre_name}.pkl", "rb") as f:
            vectorStore = pickle.load()
        
        return vectorStore