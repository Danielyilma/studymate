"""
ASGI config for studymate project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studymate.settings')
django.setup()


from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from chat import urls
from .auth import JWTAuthMiddleware 
from channels.sessions import SessionMiddlewareStack


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        SessionMiddlewareStack(  
            JWTAuthMiddleware(
                URLRouter(urls.websocket_urlpatterns)
            )
        )
    )
})


