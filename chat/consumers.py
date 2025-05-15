from channels.generic.websocket import AsyncWebsocketConsumer
import json


class AIConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # some pre work
        
        await self.accept()
    
    async def disconnect(self, code):
        # clean up memory if needed 
        pass
    
    async def receive(self, text_data=None):
        data = json.loads(text_data)
        user_message = data.get('message')
        
        ai_response = "hello, I am ai"
        
        await self.send(text_data=json.dumps(
            {
                'message' : ai_response,
            }
        ))