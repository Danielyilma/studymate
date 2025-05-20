from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async


class JWTAuthMiddleware(BaseMiddleware):
    auth = JWTAuthentication()

    async def __call__(self, scope, receive, send):
        scope['user'] = await self.authenticate(scope)

        if scope['user'].is_anonymous:
            await send({
                'type': 'websocket.close',
                'code': 4403
            })

        return await self.inner(scope, receive, send)

    async def authenticate(self, scope):
        headers = dict(scope['headers'])

        if not headers:
            return AnonymousUser()
        
        header = headers.get(b'authorization', None)

        if not header:
            return AnonymousUser()
        raw_token = self.auth.get_raw_token(header)

        if not raw_token:
            return AnonymousUser()
            
        try:
            validated_token = self.auth.get_validated_token(raw_token)
        except InvalidToken as e:
            return AnonymousUser()

        return await self.get_user(validated_token)
    
    @database_sync_to_async
    def get_user(self, validated_token):
        return self.auth.get_user(validated_token)
