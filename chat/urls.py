from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("study/chat/", consumers.AIConsumer.as_asgi()),
]