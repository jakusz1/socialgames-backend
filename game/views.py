import logging

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

import game.services as services
from .models import Game, GamePlayer, Round, Answer, Status


class GameStartView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, *args, **kwargs):
        uri = kwargs['uri']
        user = request.user
        game = Game.objects.get(uri=uri)
        player = game.players.filter(user=user, game=game)

        if game.status != "PRE" or not player.exists() or game.players.count() < 2:
            return Response(status=status.HTTP_403_FORBIDDEN)

        services.start_game(game)
        services.send(uri, 'start_game', game.to_json())

        return Response({
            'status': 'SUCCESS',
            'message': '%s started game' % user.username,
            'game': game.to_json()
        })


class GameView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        newest_game = Game.objects.filter(owner=user, status=Status.PRE.name).first()

        return Response({
            'status': 'SUCCESS',
            'game': newest_game.to_json() if newest_game else None
        })

    def post(self, request, *args, **kwargs):
        user = request.user
        game = Game.objects.create(owner=user, lang=request.data['lang'][-2:])
        GamePlayer.objects.create(user=user, game=game, color=0)

        return Response({
            'status': 'SUCCESS', 'uri': game.uri,
            'message': 'New game created'
        })

    def patch(self, request, *args, **kwargs):
        uri = kwargs['uri']
        user = request.user
        game = Game.objects.filter(uri=uri)

        if not game.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        game = game.first()
        player = game.players.filter(user=user, game=game)

        if game.status != "PRE" and not player.exists() or game.players.count() == 5:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if not player.exists():
            GamePlayer.objects.create(user=user, game=game, color=game.players.count())

        services.send(uri, 'update_players_list', game.to_json())
        return Response({
            'status': 'SUCCESS',
            'message': '%s joined game' % user.username,
            'game': game.to_json()
        })

    def delete(self, request, *args, **kwargs):
        game = Game.objects.get(uri=kwargs['uri'])
        user = request.user

        if game.owner == user:
            return Response({'status': 'SUCCESS', 'winners': services.end_game(game)})

        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


class AllRoundsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        game = Game.objects.get(uri=kwargs['uri'])
        rounds = [game_round.to_json()
                  for game_round in game.rounds.all()]

        return Response({'uri': game.uri, 'rounds': rounds})


class FirstRoundView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        game = Game.objects.get(uri=kwargs['uri'])
        first_round = game.rounds.filter(done=False).first()
        if first_round:
            game.status = Status.ANS.name
            game.save()
            services.send(kwargs['uri'], 'new_round',
                          {'id': first_round.id, 'word': first_round.text}, only_controllers=True)
            first_round.done = True
            first_round.save()
            return Response(first_round.to_json())

        return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, *args, **kwargs):
        game = Game.objects.get(uri=kwargs['uri'])
        players_stats = services.get_points(game)

        return Response({'status': 'SUCCESS',
                         'players': players_stats})


class AnswerView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        game_round = Round.objects.get(id=kwargs['round_id'])
        answers = [answer.to_json()
                   for answer in game_round.answers.all()]

        return Response({'id': game_round.id, 'answers': answers})

    def post(self, request, *args, **kwargs):
        text = request.data['text']
        user = request.user
        game_round = Round.objects.get(id=kwargs['round_id'])
        player = GamePlayer.objects.filter(user=user, game=game_round.game).first()
        Answer.objects.create(player=player, game_round=game_round, text=text)

        if services.check_if_last_answer(game_round):
            services.send(game_round.game.uri, 'all_answers', {}, only_screen=True)

        return Response({'status': 'SUCCESS'})


class UserView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user

        return Response({'username': user.username,
                         'email': user.email,
                         'total_won': user.userstats.total_won,
                         'total_score': user.userstats.total_score})

    def post(self, request, *args, **kwargs):
        user = request.user
        user.username = request.data['username']
        user.email = request.data['email']
        try:
            user.save()
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'SUCCESS',
                         'username': user.username,
                         'email': user.email})
