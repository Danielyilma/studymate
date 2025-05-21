import os
import json
import uuid
import faiss
import numpy as np
import logging
import aiohttp
import asyncio
from typing import List
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, Docx2txtLoader
from pinecone import Pinecone


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("GEMNI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")


pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index(PINECONE_INDEX_NAME)


class SessionVectorStore:
    """A class to manage document embeddings using FAISS (local) and Pinecone (cloud)."""
    
    def __init__(self, dim: int = 768, index_path: str = "session_index.faiss", map_path: str = "session_map.json"):
        """
        Initialize the SessionVectorStore.

        Args:
            dim (int): Dimension of the embedding vectors (default: 768).
            index_path (str): Path to store the FAISS index.
            map_path (str): Path to store the session map.
        """
        self.dim = dim
        self.index_path = index_path
        self.map_path = map_path

        # FAISS index with ID mapping for efficient deletion
        self.index = faiss.read_index(self.index_path) if os.path.exists(self.index_path) else faiss.IndexIDMap(faiss.IndexFlatL2(self.dim))

        # FAISS ID to session mapping
        self.session_map = self._load_map()

        # Embedding model
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=API_KEY
        )

    def _load_map(self) -> dict:
        """Load the session map from disk."""
        if os.path.exists(self.map_path):
            with open(self.map_path, "r") as f:
                return json.load(f)
        return {}

    def _save_index(self) -> None:
        """Save the FAISS index and session map to disk."""
        faiss.write_index(self.index, self.index_path)
        with open(self.map_path, "w") as f:
            json.dump(self.session_map, f, indent=2)

    async def _download_file(self, url: str) -> str:
        """Download a file from a URL and return the temporary file path."""
        ext = url.split("?")[0].split("/")[-1].lower()
        filename = f"/tmp/{uuid.uuid4().hex}.{ext}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                with open(filename, "wb") as f:
                    f.write(await response.read())
        return filename

    def _get_loader(self, file_path: str) -> tuple:
        """
        Get the appropriate document loader for the file.

        Args:
            file_path (str): Path or URL to the file.

        Returns:
            tuple: (loader, temp_file_path or None)
        """
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

    def store_embeddings(self, file_path: str, session_id: str) -> None:
        """
        Store document embeddings for a session in FAISS and Pinecone.

        Args:
            file_path (str): Path or URL to the document.
            session_id (str): Unique identifier for the session.

        Raises:
            ValueError: If session_id is invalid or file format is unsupported.
        """
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id must be a non-empty string")

        if session_id in self.session_map:
            logger.info(f"Embeddings already exist for session {session_id}")
            return

        loader, temp_file = self._get_loader(file_path)
        try:
            docs: List[Document] = loader.load()
            texts = [doc.page_content for doc in docs]

            embeddings = self.embedding_model.embed_documents(texts)
            embeddings_np = np.array(embeddings).astype("float32")

            # Store in FAISS
            start_id = self.index.ntotal
            faiss_ids = np.array(list(range(start_id, start_id + len(embeddings))), dtype=np.int64)
            self.index.add_with_ids(embeddings_np, faiss_ids)
            self.session_map[session_id] = faiss_ids.tolist()
            self._save_index()

            # Store in Pinecone with batching
            batch_size = 100
            pinecone_vectors = [
                {
                    "id": f"{session_id}_{i}",
                    "values": embedding,
                    "metadata": {"session_id": session_id}
                }
                for i, embedding in enumerate(embeddings_np)
            ]
            for i in range(0, len(pinecone_vectors), batch_size):
                pinecone_index.upsert(vectors=pinecone_vectors[i:i + batch_size])

            logger.info(f"Stored {len(embeddings)} vectors for session {session_id} to FAISS and Pinecone")
        finally:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)

    def load_embeddings(self, session_id: str) -> np.ndarray:
        """
        Load embeddings for a session from FAISS or Pinecone.

        Args:
            session_id (str): Session identifier.

        Returns:
            np.ndarray: Array of embeddings.

        Raises:
            ValueError: If session_id is invalid or no embeddings are found.
        """
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id must be a non-empty string")

        if session_id in self.session_map:
            ids = self.session_map[session_id]
            logger.info(f"Loading {len(ids)} vectors for session {session_id} from FAISS")
            return np.array([self.index.reconstruct(i) for i in ids])

        logger.info(f"FAISS does not have session {session_id}. Falling back to Pinecone...")

        # Fetch vectors from Pinecone
        pinecone_ids = [f"{session_id}_{i}" for i in range(1000)]  # Limited to avoid excessive queries
        response = pinecone_index.fetch(ids=pinecone_ids)

        embeddings = [response.vectors[id].values for id in response.vectors if id in response.vectors]
        if not embeddings:
            raise ValueError(f"No embeddings found in Pinecone for session {session_id}")

        embeddings_np = np.array(embeddings).astype("float32")

        # Cache to FAISS
        start_id = self.index.ntotal
        faiss_ids = np.array(list(range(start_id, start_id + len(embeddings))), dtype=np.int64)
        self.index.add_with_ids(embeddings_np, faiss_ids)
        self.session_map[session_id] = faiss_ids.tolist()
        self._save_index()

        logger.info(f"Pulled {len(embeddings)} vectors from Pinecone and cached to FAISS")

        return embeddings_np

    def delete_session(self, session_id: str) -> None:
        """
        Delete embeddings for a session from FAISS and Pinecone.

        Args:
            session_id (str): Session identifier.

        Raises:
            ValueError: If session_id is invalid.
        """
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id must be a non-empty string")

        if session_id in self.session_map:
            faiss_ids = np.array(self.session_map[session_id], dtype=np.int64)
            self.index.remove_ids(faiss_ids)
            del self.session_map[session_id]
            self._save_index()
            logger.info(f"Deleted session {session_id} from FAISS")

        # Delete from Pinecone
        pinecone_ids = [f"{session_id}_{i}" for i in range(1000)]  # Limited to avoid excessive queries
        response = pinecone_index.fetch(ids=pinecone_ids)
        valid_ids = [id for id in response.vectors if id in response.vectors]
        if valid_ids:
            pinecone_index.delete(ids=valid_ids)
            logger.info(f"Deleted session {session_id} from Pinecone")
        else:
            logger.warning(f"No vectors found in Pinecone for session {session_id}")

    def has_embeddings(self, session_id: str) -> bool:
        """
        Check if embeddings exist for a session.

        Args:
            session_id (str): Session identifier.

        Returns:
            bool: True if embeddings exist, False otherwise.

        Raises:
            ValueError: If session_id is invalid.
        """
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id must be a non-empty string")

        if session_id in self.session_map:
            return True

        try:
            pinecone_ids = [f"{session_id}_{i}" for i in range(1)]  # Check one ID for efficiency
            response = pinecone_index.fetch(ids=pinecone_ids)
            return bool(response.vectors)
        except Exception as e:
            logger.error(f"Pinecone check failed for session {session_id}: {e}")
            return False