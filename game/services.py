import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from faker import Faker

from game.daily_trends import DailyTrends
from game.selenium_trends import SeleniumTrends

from game.models import Round, Lang, Status
from socialgames.settings import GAME_SETTINGS


def send(uri, command, data, only_screen=False, only_controllers=False):
    channel_layer = get_channel_layer()
    if not only_controllers:
        async_to_sync(channel_layer.group_send)(uri, {"type": "broadcast",
                                                      "response": {
                                                          "command": command,
                                                          "data": data
                                                      }})
    if not only_screen:
        async_to_sync(channel_layer.group_send)(uri + GAME_SETTINGS['controller_postfix'],
                                                {"type": "broadcast",
                                                 "response": {
                                                     "command": command,
                                                     "data": data
                                                 }})


def start_game(game):
    faker = Faker(Lang[game.lang].value)
    faker_words = faker.words(nb=6)
    daily_words = DailyTrends().get_words(game.lang, 3)

    # round 1
    Round.objects.create(game=game, text=faker_words[0], multiplier=1)
    Round.objects.create(game=game, text=faker_words[1], multiplier=1)
    Round.objects.create(game=game, text=daily_words[0], multiplier=1)
    # round 2
    Round.objects.create(game=game, text=faker_words[2], multiplier=2)
    Round.objects.create(game=game, text=faker_words[3], multiplier=2)
    Round.objects.create(game=game, text=daily_words[1], multiplier=2)
    # round 3
    Round.objects.create(game=game, text=faker_words[4], multiplier=3)
    Round.objects.create(game=game, text=faker_words[5], multiplier=3)
    Round.objects.create(game=game, text=daily_words[2], multiplier=3)

    game.status = Status.IDL.name
    game.save()


def check_if_last_answer(game_round):
    return game_round.game.players.count() == game_round.answers.count()


def send_question(game):
    game_round = game.rounds.filter(done=False).first()
    if game_round:
        send(game.uri, 'new_round', game_round.to_json())
        game_round.done = True
        game_round.game.status = Status.ANS.name
        game_round.save()
        return True
    return False


def get_points(game):
    game_round = game.rounds.filter(done=True).first()
    if game_round:
        game.status = Status.IDL.name
        game.save()

        answers = game_round.answers.order_by("player_id").all()
        data = SeleniumTrends().get_data([answer.text for answer in answers], game.lang)

        if not data.empty:
            scores = dict(zip(data.columns.values.tolist(), data.iloc[-1]))
            for answer in answers:
                multiplied_score = int(int(scores.get(answer.text)) * game_round.multiplier)
                answer.score = multiplied_score
                answer.player.score += multiplied_score
                answer.save()
                answer.player.save()
            send(game.uri, "results_graph", data.to_json(orient="split"), only_screen=True)
            send(game.uri, "results_answers", json.dumps([answer.to_json() for answer in answers]), only_screen=True)
            send(game.uri, "send_players_silent", game.to_json(), only_screen=True)
            game_round.delete()
            return [player.to_json() for player in game.players.order_by("-score").all()]
        else:
            send(game.uri, "results_graph", "{}",
                 only_screen=True)
            send(game.uri, "results_answers", json.dumps([answer.to_json() for answer in answers]),
                 only_screen=True)
            game_round.delete()
            return [player.to_json() for player in game.players.order_by("-score").all()]

    send(game.uri, 'go_back', {})
    game.delete()
    return [player.to_json() for player in game.players.order_by("-score").all()]


def end_game(game):
    final_players_list_json = []
    for index, player in enumerate(game.players.order_by("-score").all()):
        final_players_list_json.append(player.to_json())
        player.user.userstats.total_score += player.score
        if index == 0:
            player.user.userstats.total_won += 1
        player.user.save()

    send(game.uri, 'go_back', {}, only_controllers=True)
    game.delete()
    return final_players_list_json
