import os
import json
import uuid
import faiss
import numpy as np
import logging
import aiohttp
import asyncio
import redis
from typing import List
from asgiref.sync import sync_to_async
from dotenv import load_dotenv
from langchain_core.documents import Document as LangchainDocument
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, Docx2txtLoader
from pinecone import Pinecone
from study_tools.models import File, Session
from django.contrib.auth import get_user_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("GEMNI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

class SessionVectorStore:
    """A class to manage document embeddings using FAISS (local) and Pinecone (cloud)."""
    
    def __init__(self, dim: int = 768, index_path: str = "session_index.faiss", map_path: str = "session_map.json"):
        self.dim = dim
        self.index_path = index_path
        self.map_path = map_path
        self.index = faiss.read_index(self.index_path) if os.path.exists(self.index_path) else faiss.IndexIDMap(faiss.IndexFlatL2(self.dim))
        self.session_map = self._load_map()
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=API_KEY
        )
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        self.pinecone_index = Pinecone(api_key=PINECONE_API_KEY).Index(PINECONE_INDEX_NAME)

    def _load_map(self) -> dict:
        if os.path.exists(self.map_path):
            with open(self.map_path, "r") as f:
                return json.load(f)
        return {}

    def _save_index(self) -> None:
        faiss.write_index(self.index, self.index_path)
        with open(self.map_path, "w") as f:
            json.dump(self.session_map, f, indent=2)

    async def _download_file(self, url: str) -> str:
        ext = url.split("?")[0].split("/")[-1].lower()
        filename = f"/tmp/{uuid.uuid4().hex}.{ext}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                with open(filename, "wb") as f:
                    f.write(await response.read())
        return filename

    def _get_loader(self, file_path: str) -> tuple:
        temp_file = None
        if file_path.startswith("http://") or file_path.startswith("https://"):
            loop = asyncio.get_event_loop()
            file_path = loop.run_until_complete(self._download_file(file_path))
            temp_file = file_path

        if file_path.endswith(".pdf"):
            loader = PyMuPDFLoader(file_path)
        elif file_path.endswith(".txt"):
            loader = TextLoader(file_path)
        elif file_path.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        else:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            raise ValueError("Unsupported file format")
        
        return loader, temp_file

    async def store_embeddings(self, file_path: str, session_id: str, user_id: int) -> None:
        """
        Store document embeddings, metadata, and text for a session.
        """
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id must be a non-empty string")
        if not user_id or not isinstance(user_id, int):
            raise ValueError("user_id must be a valid integer")

        if session_id in self.session_map:
            logger.info(f"Embeddings already exist for session {session_id}")
            return

        User = get_user_model()
        try:
            user = await sync_to_async(User.objects.get)(id=user_id)
            session = await sync_to_async(Session.objects.get)(session_id=session_id, user=user)
        except User.DoesNotExist:
            logger.error(f"User with id {user_id} does not exist")
            raise ValueError(f"User with id {user_id} does not exist")
        except Session.DoesNotExist:
            logger.error(f"Session with id {session_id} does not exist for user {user_id}")
            raise ValueError(f"Session with id {session_id} does not exist")

        loader, temp_file = self._get_loader(file_path)
        try:
            docs: List[LangchainDocument] = loader.load()
            texts = [doc.page_content for doc in docs]

            # Store in File model
            file_obj, created = await sync_to_async(File.objects.update_or_create)(
                session=session,
                defaults={"url": file_path}
            )
            logger.info(f"Stored/updated File entry for session {session_id} with URL {file_path}")

            # Store text in Redis
            try:
                async def execute_pipeline():
                    pipe = self.redis_client.pipeline()
                    for i, text in enumerate(texts):
                        key = f"doc:{session_id}:{i}"
                        pipe.set(key, text)
                        pipe.expire(key, 30 * 24 * 3600)
                    return pipe.execute()
                await sync_to_async(execute_pipeline)()
                logger.info(f"Stored {len(texts)} document chunks for session {session_id} in Redis")
            except Exception as e:
                logger.error(f"Failed to store text in Redis: {e}")

            embeddings = self.embedding_model.embed_documents(texts)
            embeddings_np = np.array(embeddings).astype("float32")

            # Store in FAISS
            start_id = self.index.ntotal
            faiss_ids = np.array(list(range(start_id, start_id + len(embeddings))), dtype=np.int64)
            self.index.add_with_ids(embeddings_np, faiss_ids)
            self.session_map[session_id] = faiss_ids.tolist()
            self._save_index()

            # Store in Pinecone with text metadata
            batch_size = 100
            pinecone_vectors = [
                {
                    "id": f"{session_id}_{i}",
                    "values": embedding,
                    "metadata": {"session_id": session_id, "text": text[:40000]}
                }
                for i, (embedding, text) in enumerate(zip(embeddings_np, texts))
            ]
            for i in range(0, len(pinecone_vectors), batch_size):
                self.pinecone_index.upsert(vectors=pinecone_vectors[i:i + batch_size])

            logger.info(f"Stored {len(embeddings)} vectors for session {session_id} to FAISS and Pinecone")
        finally:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)

    def load_embeddings(self, session_id: str) -> np.ndarray:
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id must be a non-empty string")

        if session_id in self.session_map:
            ids = self.session_map[session_id]
            logger.info(f"Loading {len(ids)} vectors for session {session_id} from FAISS")
            return np.array([self.index.reconstruct(i) for i in ids])

        logger.info(f"FAISS does not have session {session_id}. Falling back to Pinecone...")
        pinecone_ids = [f"{session_id}_{i}" for i in range(1000)]
        response = self.pinecone_index.fetch(ids=pinecone_ids)
        embeddings = [response.vectors[id].values for id in response.vectors if id in response.vectors]
        if not embeddings:
            raise ValueError(f"No embeddings found in Pinecone for session {session_id}")

        embeddings_np = np.array(embeddings).astype("float32")
        start_id = self.index.ntotal
        faiss_ids = np.array(list(range(start_id, start_id + len(embeddings))), dtype=np.int64)
        self.index.add_with_ids(embeddings_np, faiss_ids)
        self.session_map[session_id] = faiss_ids.tolist()
        self._save_index()
        logger.info(f"Pulled {len(embeddings)} vectors from Pinecone and cached to FAISS")
        return embeddings_np

    async def delete_session(self, session_id: str) -> None:
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id must be a non-empty string")

        # Delete from File model
        try:
            session = await sync_to_async(Session.objects.get)(session_id=session_id)
            await sync_to_async(File.objects.filter(session=session).delete)()
            logger.info(f"Deleted File entries for session {session_id}")
        except Session.DoesNotExist:
            logger.warning(f"No Session found for session_id {session_id}")

        # Delete text from Redis
        try:
            keys = await sync_to_async(self.redis_client.keys)(f"doc:{session_id}:*")
            if keys:
                await sync_to_async(self.redis_client.delete)(*keys)
                logger.info(f"Deleted {len(keys)} document chunks for session {session_id} from Redis")
        except Exception as e:
            logger.error(f"Failed to delete text from Redis: {e}")

        if session_id in self.session_map:
            faiss_ids = np.array(self.session_map[session_id], dtype=np.int64)
            self.index.remove_ids(faiss_ids)
            del self.session_map[session_id]
            self._save_index()
            logger.info(f"Deleted session {session_id} from FAISS")

        pinecone_ids = [f"{session_id}_{i}" for i in range(1000)]
        response = self.pinecone_index.fetch(ids=pinecone_ids)
        valid_ids = [id for id in response.vectors if id in response.vectors]
        if valid_ids:
            self.pinecone_index.delete(ids=valid_ids)
            logger.info(f"Deleted session {session_id} from Pinecone")
        else:
            logger.warning(f"No vectors found in Pinecone for session {session_id}")

    def has_embeddings(self, session_id: str) -> bool:
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id must be a non-empty string")

        if session_id in self.session_map:
            return True

        try:
            pinecone_ids = [f"{session_id}_0"]
            response = self.pinecone_index.fetch(ids=pinecone_ids)
            return bool(response.vectors)
        except Exception as e:
            logger.error(f"Pinecone check failed for session {session_id}: {e}")
            return False