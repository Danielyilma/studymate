import json
import numpy as np
import logging
import redis
import aiohttp
import asyncio
import os
import uuid
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from ai_tools.template import chat_template
from ai_tools.mixins import BaseClient
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from ai_tools.faiss_loader import SessionVectorStore
from study_tools.models import File, Session
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, Docx2txtLoader
from django.conf import settings

logger = logging.getLogger(__name__)

class AIChat(BaseClient):
    """A class to handle AI chat with document context and conversation memory for a Django app."""
    
    def __init__(self, session_vector_store: SessionVectorStore, max_history: int = 10):
        self.vector_store = session_vector_store
        self.max_history = max_history
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )
        self.chat_prompt = ChatPromptTemplate.from_template(chat_template)
        self.chat_chain = (
            {
                "context": self._retrieve_context,
                "history": RunnablePassthrough(),
                "question": RunnablePassthrough()
            } | self.chat_prompt | self.llm | StrOutputParser()
        ).with_config({"verbose": True})

    async def _download_and_load_text(self, url: str) -> str:
        """Download a file from a URL and extract text using appropriate loader."""
        ext = url.split("?")[0].split("/")[-1].lower()
        filename = f"/tmp/{uuid.uuid4().hex}.{ext}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    with open(filename, "wb") as f:
                        f.write(await response.read())
            
            if ext.endswith(".pdf"):
                loader = PyMuPDFLoader(filename)
            elif ext.endswith(".txt"):
                loader = TextLoader(filename)
            elif ext.endswith(".docx"):
                loader = Docx2txtLoader(filename)
            else:
                raise ValueError(f"Unsupported file format: {ext}")
            
            docs = loader.load()
            text = "\n".join(doc.page_content for doc in docs)
            logger.info(f"Extracted text from {url}")
            return text
        except Exception as e:
            logger.error(f"Failed to download or load text from {url}: {e}")
            return ""
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    async def _retrieve_context(self, input_data: dict) -> str:
        """
        Retrieve relevant document text context for a query from Redis.
        """
        query = input_data.get("question", "")
        session_id = input_data.get("document_session_id", "")
        
        if not self.vector_store.has_embeddings(session_id):
            logger.warning(f"No embeddings found for session {session_id}")
            return "No relevant document context found."
        
        # Try Redis
        try:
            query_embedding = self.vector_store.embedding_model.embed_query(query)
            query_embedding_np = np.array([query_embedding]).astype("float32")
            k = 3
            D, I = self.vector_store.index.search(query_embedding_np, k)
            context = []
            for idx in I[0]:
                if idx != -1:
                    text = await sync_to_async(self.redis_client.get)(f"doc:{session_id}:{idx}")
                    if text:
                        context.append(text)
            context_str = "\n".join(context) if context else "No relevant document text found."
            if context:
                logger.info(f"Retrieved {len(context)} document chunks for session {session_id} from Redis")
                return context_str
        except Exception as e:
            logger.error(f"Failed to retrieve text from Redis: {e}")

        # Fallback to File model (cloud download)
        try:
            session = await sync_to_async(Session.objects.get)(id=session_id)
            files = await sync_to_async(lambda: list(File.objects.filter(session=session)[:3]))()
            if files:
                context = []
                for file in files:
                    text = await self._download_and_load_text(file.url)
                    if text:
                        context.append(text)
                context_str = "\n".join(context)
                logger.info(f"Retrieved {len(context)} document texts for session {session_id} from File model")
                return context_str if context_str else "No relevant document text found."
        except Session.DoesNotExist:
            logger.warning(f"No Session found for session_id {session_id}")
        except Exception as e:
            logger.error(f"Failed to retrieve document text from File model: {e}")

        # Fallback to Pinecone metadata
        try:
            results = await sync_to_async(self.vector_store.pinecone_index.query)(
                vector=query_embedding,
                top_k=3,
                include_metadata=True,
                filter={"session_id": session_id}
            )
            context = []
            for match in results['matches']:
                text = match['metadata'].get('text', f"Document {session_id}: [Content not found]")
                context.append(text)
            context_str = "\n".join(context) if context else "No relevant document context found."
            logger.info(f"Retrieved {len(context)} document texts for session {session_id} from Pinecone metadata")
            return context_str
        except Exception as e:
            logger.error(f"Failed to retrieve context from Pinecone: {e}")

        # Fallback to embedding-based placeholder
        try:
            query_embedding_np = np.array([query_embedding]).astype("float32")
            k = 3
            D, I = self.vector_store.index.search(query_embedding_np, k)
            context = []
            for idx in I[0]:
                if idx != -1:
                    for sess_id, ids in self.vector_store.session_map.items():
                        if idx in ids and sess_id == session_id:
                            context.append(f"Document {sess_id}: [Content not directly stored, embeddings used for context]")
                            break
            context_str = "\n".join(context) if context else "No relevant document context found."
            logger.info(f"Fell back to embedding-based context for session {session_id}")
            return context_str
        except Exception as e:
            logger.error(f"Failed to retrieve embedding-based context: {e}")
            return "No relevant document context found."

    async def chat(self, user_id: int, document_session_id: str, query: str) -> str:
        """
        Handle a chat query with document context and conversation memory.
        """
        if not user_id or not isinstance(user_id, int):
            raise ValueError("user_id must be a valid integer")
        if not document_session_id or not isinstance(document_session_id, str):
            raise ValueError("document_session_id must be a non-empty string")
        
        if not self.vector_store.has_embeddings(document_session_id):
            logger.warning(f"No embeddings found for document session {document_session_id}")
            raise ValueError(f"No embeddings found for document session {document_session_id}")

        User = get_user_model()
        try:
            await sync_to_async(User.objects.get)(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User with id {user_id} does not exist")
            raise ValueError(f"User with id {user_id} does not exist")

        cache_key = f"chat:{user_id}:{document_session_id}"
        try:
            history = await sync_to_async(self.redis_client.lrange)(cache_key, 0, self.max_history * 2 - 1)
            chat_history = [
                HumanMessage(content=json.loads(msg)['content']) if json.loads(msg)['type'] == 'human'
                else AIMessage(content=json.loads(msg)['content'])
                for msg in history
            ]
            logger.info(f"Loaded chat history from Redis for user {user_id}, document {document_session_id}")
        except Exception as e:
            logger.error(f"Failed to load chat history from Redis: {e}")
            chat_history = []

        chat_history.append(HumanMessage(content=query))
        if len(chat_history) > self.max_history * 2:
            chat_history = chat_history[-self.max_history * 2:]

        history_str = "\n".join([f"{'Human' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" for msg in chat_history])

        try:
            response = await self.chat_chain.ainvoke({
                "question": query,
                "history": history_str,
                "document_session_id": document_session_id
            })
            logger.info(f"Generated response for query: {query[:50]}...")
        except Exception as e:
            logger.error(f"Chat chain invocation failed: {e}")
            raise

        try:
            def execute_pipeline():
                pipe = self.redis_client.pipeline()
                pipe.lpush(cache_key, json.dumps({'type': 'human', 'content': query}))
                pipe.lpush(cache_key, json.dumps({'type': 'ai', 'content': response}))
                pipe.ltrim(cache_key, 0, self.max_history * 2 - 1)
                pipe.expire(cache_key, 7 * 24 * 3600)
                return pipe.execute()
            await sync_to_async(execute_pipeline)()
            logger.info(f"Saved chat history to Redis for user {user_id}, document {document_session_id}")
        except Exception as e:
            logger.error(f"Failed to save chat history to Redis: {e}")

        return response