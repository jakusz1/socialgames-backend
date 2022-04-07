from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path

from game.consumers import GameConsumer


application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r"^ws/(?P<device_type>\w*)/(?P<uri>\w*)$", GameConsumer)
        ])
    ),
})
