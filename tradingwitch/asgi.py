import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from fyersapi.routing import ws_urlpatterns  # Ensure this import is correct

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradingwitch.settings')

# Regular Django ASGI application
django_asgi_application = get_asgi_application()

# Django Channels WebSocket application
application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,  # This should be "http"
        "websocket": AuthMiddlewareStack(
            URLRouter(
                ws_urlpatterns  # Use your WebSocket URL patterns
            )
        ),
    }
)
