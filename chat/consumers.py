# your_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .services import VectorStoreSingleton
from ai_tools.AI_Chat import AIChat

class AIConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.vector_store = VectorStoreSingleton.get_instance()
        self.ai_chat = AIChat(self.vector_store)
        
        # Ensure Django session is saved for history persistence
        if not self.scope['session'].session_key:
            self.scope['session'].save()
        
        await self.accept()

    async def disconnect(self, code):
        pass

    async def receive(self, text_data=None):
        try:
            data = json.loads(text_data)
            query = data.get('query')
            document_session_id = data.get('document_session_id')
            django_session_id = self.scope['session'].session_key

            if not query or not document_session_id or not django_session_id:
                await self.send(text_data=json.dumps({
                    'error': 'Missing query, document_session_id, or session'
                }))
                return

            # Process chat query using AIChat
            response = await sync_to_async(self.ai_chat.chat)(
                django_session_id,
                document_session_id,
                query
            )
            await self.send(text_data=json.dumps({
                'message': response
            }))
        except ValueError as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': 'Internal server error'
            }))