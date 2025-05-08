import os
import pinecone
from dotenv import load_dotenv


PINECONE_API_KEY=os.environ.get('PINECONE_API_KEY')
pinecone.init(api_key= PINECONE_API_KEY, environment="env") 
index = pinecone.Index("") 