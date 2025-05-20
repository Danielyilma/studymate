import json
import numpy as np
from ai_tools.template import chat_template
from ai_tools.mixins import BaseClient
from django.contrib.sessions.models import Session
from django.core.serializers.json import DjangoJSONEncoder
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from ai_tools.faiss_loader import SessionVectorStore


class AIChat(BaseClient):
    """A class to handle AI chat with document context and conversation memory for a Django app."""
    
    def __init__(self, session_vector_store: SessionVectorStore, max_history: int = 10):
        """
        Initialize the AIChat system.

        Args:
            session_vector_store (SessionVectorStore): Instance of SessionVectorStore for embeddings.
            max_history (int): Maximum number of past messages to retain in memory per session.
        """
        self.vector_store = session_vector_store
        self.max_history = max_history
             
        self.chat_prompt = ChatPromptTemplate.from_template(chat_template)
        
        # Set up chat chain
        self.chat_chain = (
            {
                "context": self._retrieve_context,
                "history": RunnablePassthrough(),
                "question": RunnablePassthrough()
            } | self.chat_prompt | self.llm | StrOutputParser()
        ).with_config({"verbose": True})

    def _retrieve_context(self, input_data: dict) -> str:
        """
        Retrieve relevant document context for a query.

        Args:
            input_data (dict): Dictionary containing 'query' and 'document_session_id'.

        Returns:
            str: Concatenated context from relevant documents.
        """
        query = input_data.get("question", "")
        session_id = input_data.get("document_session_id", "")
        
        if not self.vector_store.has_embeddings(session_id):
            return "No relevant document context found."
        
        # Embed the query
        query_embedding = self.vector_store.embedding_model.embed_query(query)
        query_embedding_np = np.array([query_embedding]).astype("float32")
        
        # Search FAISS index for top-k similar documents
        k = 3
        D, I = self.vector_store.index.search(query_embedding_np, k)
        
        # Reconstruct context from FAISS IDs
        context = []
        for idx in I[0]:
            if idx != -1:  # Valid index
                for sess_id, ids in self.vector_store.session_map.items():
                    if idx in ids and sess_id == session_id:
                        context.append(f"Document {sess_id}: [Content not directly stored, embeddings used for context]")
                        break
        
        
        return "\n".join(context) if context else "No relevant document context found."

    def chat(self, django_session_id: str, document_session_id: str, query: str) -> str:
        """
        Process a chat query with document context and conversation history.

        Args:
            django_session_id (str): Django session ID for user-specific chat history.
            document_session_id (str): Session ID for document embeddings.
            query (str): User's question or input.

        Returns:
            str: AI's response.

        Raises:
            ValueError: If session IDs are invalid or no embeddings are found.
        """
        if not django_session_id or not isinstance(django_session_id, str):
            raise ValueError("django_session_id must be a non-empty string")
        if not document_session_id or not isinstance(document_session_id, str):
            raise ValueError("document_session_id must be a non-empty string")
        
        # Ensure embeddings exist for the document session
        if not self.vector_store.has_embeddings(document_session_id):
            raise ValueError(f"No embeddings found for document session {document_session_id}")

        # Load chat history from Django session
        try:
            session = Session.objects.get(session_key=django_session_id)
            session_data = session.get_decoded()
            chat_history = session_data.get('chat_history', [])
            chat_history = [
                HumanMessage(content=msg['content']) if msg['type'] == 'human'
                else AIMessage(content=msg['content'])
                for msg in chat_history
            ]
        except Session.DoesNotExist:
            chat_history = []

        
        chat_history.append(HumanMessage(content=query))
        if len(chat_history) > self.max_history * 2:
            chat_history = chat_history[-self.max_history * 2:]

        # Format history for the prompt
        history_str = "\n".join([f"{'Human' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" for msg in chat_history])

        # Invoke chat chain

        # print("history", history_str, django_session_id)
        
        response = self.chat_chain.invoke({
            "question": query,
            "history": history_str,
            "document_session_id": document_session_id
        })
        
        # Save messages to Django session
        # print(response, "ai res")
        
        session_data = session_data if 'session_data' in locals() else {}
        print(session_data)
        session_data['chat_history'] = [
            {'type': 'human' if isinstance(msg, HumanMessage) else 'ai', 'content': msg.content}
            for msg in chat_history
        ]
        Session.objects.update_or_create(
            session_key=django_session_id,
            defaults={'session_data': json.dumps(session_data, cls=DjangoJSONEncoder)}
        )

                
        return response



