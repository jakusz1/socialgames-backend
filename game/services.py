import datetime
import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from faker import Faker
from pytrends.request import TrendReq

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


def start_game(game, *args):
    if not args:
        faker = Faker(Lang[game.lang].value)
        args = faker.words(nb=10, ext_word_list=None)

    for arg in args:
        Round.objects.create(game=game, text=arg)

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
        pytrends = TrendReq(hl=game.lang, tz=0)

        answers = game_round.answers.order_by("player_id").all()
        answers_text_list = [answer.text for answer in answers]

        now = datetime.datetime.now()
        date = now - datetime.timedelta(days=365)

        try:
            pytrends.build_payload(answers_text_list, cat=0,
                                   timeframe=date.strftime("%Y-%m-%d") + ' ' + now.strftime("%Y-%m-%d"),
                                   geo=game.lang,
                                   gprop='')
            scrapped_df = pytrends.interest_over_time()
        except:
            send(game.uri, "results_graph", "{}",
                 only_screen=True)
            send(game.uri, "results_answers", json.dumps([answer.to_json() for answer in answers]),
                 only_screen=True)
            game_round.delete()
            return False

        if scrapped_df.size != 0:
            scrapped_df = scrapped_df.drop(columns='isPartial')[:-1]
            scores = dict(zip(scrapped_df.columns.values.tolist(), scrapped_df.iloc[-1]))
            for answer in answers:
                answer.score = int(scores.get(answer.text))
                answer.player.score += int(scores.get(answer.text))
                answer.save()
                answer.player.save()
            send(game.uri, "results_graph", '{' + scrapped_df.to_json(orient="split")[1:-1] + '}',
                 only_screen=True)
            send(game.uri, "results_answers", json.dumps([answer.to_json() for answer in answers]),
                 only_screen=True)
            send(game.uri, "send_players_silent", game.to_json(), only_screen=True)
            game_round.delete()
            return True
        else:
            send(game.uri, "results_graph", "{}",
                 only_screen=True)
            send(game.uri, "results_answers", json.dumps([answer.to_json() for answer in answers]),
                 only_screen=True)
            game_round.delete()
            return False

    send(game.uri, 'go_back', {})
    game.delete()
    return False


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
