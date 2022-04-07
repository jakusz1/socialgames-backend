from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync

from game.models import Game
import game.services as services
from socialgames.settings import GAME_SETTINGS


class GameConsumer(JsonWebsocketConsumer):

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            self.__get_uri(),
            self.channel_name
        )
        self.accept()

    def receive_json(self, content, **kwargs):
        uri = self.__get_uri()

        command = content.get("command", None)
        content['user'] = self.scope['user']
        content['game'] = Game.objects.get(uri=uri)
        method = getattr(self, command, self.wrong_command)
        method(content)

    def wrong_command(self, content):
        self.send_response({
            "error": "Command not supported"
        })

    def start_game(self, content):
        services.start_game(content['game'])

    def out_of_time(self, content):
        async_to_sync(self.channel_layer.group_send)(
            self.__get_uri() + GAME_SETTINGS['controller_postfix'],
            {
                "type": "broadcast",
                "response": {"command": "out_of_time"}
            })

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.__get_uri(),
            self.channel_name,
        )
        self.send_json({
            "command": "disconnect",
            "response": "disconnected"
        })

    def send_response(self, response, broadcast=True):
        if broadcast:
            async_to_sync(self.channel_layer.group_send)(
                self.__get_uri(),
                {
                    "type": "broadcast",
                    "response": response
                })
        else:
            self.send_json(response)

    def broadcast(self, content):
        self.send_json(content["response"])

    def __get_uri(self):
        if self.scope["url_route"]["kwargs"]["device_type"] == "games":
            return self.scope["url_route"]["kwargs"]["uri"]
        else:
            return self.scope["url_route"]["kwargs"]["uri"] + GAME_SETTINGS['controller_postfix']
