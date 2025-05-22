import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from .services import VectorStoreSingleton
from ai_tools.AI_Chat import AIChat

logger = logging.getLogger(__name__)

class AIConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            user = self.scope['user']
            User = get_user_model()
            if not isinstance(user, User) or not user.is_authenticated:
                logger.error("Unauthenticated user attempted WebSocket connection")
                await self.close(code=4403)  # Match JWTAuthMiddleware
                return

            self.user = user
            self.vector_store = VectorStoreSingleton.get_instance()
            self.ai_chat = AIChat(self.vector_store)
            await self.accept()
            logger.info(f"WebSocket connected for user {user.id}")
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            await self.close(code=4403)

    async def disconnect(self, code):
        logger.info(f"WebSocket disconnected with code {code}")

    async def receive(self, text_data=None):
        try:
            data = json.loads(text_data)
            query = data.get('query')
            document_session_id = data.get('session_id')

            if not query or not document_session_id:
                error_msg = 'Missing query or document_session_id'
                logger.warning(f"Invalid input: {error_msg}")
                await self.send(text_data=json.dumps({'error': error_msg}))
                return

            # Process chat query using AIChat
            response = await self.ai_chat.chat(
                self.user.id, document_session_id, query
            )
            await self.send(text_data=json.dumps({'message': response}))
            logger.info(f"Sent response for query: {query[:50]}...")
        except ValueError as e:
            logger.error(f"ValueError in receive: {e}")
            await self.send(text_data=json.dumps({'error': str(e)}))
        except Exception as e:
            logger.error(f"Unexpected error in receive: {e}")
            await self.send(text_data=json.dumps({'error': 'Internal server error'}))