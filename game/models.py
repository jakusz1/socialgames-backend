import random
import string
from enum import Enum

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from socialgames.settings import GAME_SETTINGS


class ChoiceEnum(Enum):
    @classmethod
    def choices(cls):
        return [(choice.name, choice.value) for choice in cls]


class Lang(ChoiceEnum):
    US = "en_US"
    PL = "pl_PL"


class Status(ChoiceEnum):
    PRE = "not_started"
    IDL = "started_not_answering"
    ANS = "started_answering"


def _generate_unique_uri():
    all_chars = string.ascii_lowercase
    return "".join(random.choice(all_chars) for _ in range(GAME_SETTINGS["code_length"]))


class Game(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    uri = models.CharField(max_length=GAME_SETTINGS["code_length"],
                           default=_generate_unique_uri)
    lang = models.CharField(max_length=2,
                            choices=Lang.choices(),
                            default=Lang.PL.name)
    status = models.CharField(max_length=3,
                              choices=Status.choices(),
                              default=Status.PRE.name)
    created_at = models.DateTimeField(auto_now_add=True)

    def to_json(self):
        return {"id": self.id,
                "lang": self.lang,
                "status": self.status,
                "players": [player.to_json()
                            for player in self.players.all()],
                "rounds": self.rounds.count(),
                "uri": self.uri,
                "created_at": self.created_at.isoformat()}


class GamePlayer(models.Model):
    game = models.ForeignKey(
        Game, related_name="players", on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    color = models.IntegerField(default=0)

    def to_json(self):
        return {"id": self.id,
                "username": self.user.username,
                "email": self.user.email,
                "score": self.score,
                "total_score": self.user.userstats.total_score,
                "total_won": self.user.userstats.total_won,
                "color": self.color}


class Round(models.Model):
    game = models.ForeignKey(Game, related_name="rounds", on_delete=models.CASCADE)
    text = models.TextField(max_length=50)
    done = models.BooleanField(default=False)
    multiplier = models.FloatField(default=1)

    def to_json(self):
        return {"id": self.id, "text": self.text, "done": self.done, "multiplier": self.multiplier}


class Answer(models.Model):
    player = models.ForeignKey(GamePlayer, on_delete=models.CASCADE)
    game_round = models.ForeignKey(Round, related_name="answers", on_delete=models.CASCADE)
    text = models.TextField(max_length=100)
    score = models.IntegerField(default=0)

    def to_json(self):
        return {"username": self.player.user.username,
                "player_id": self.player.id,
                "id": self.id,
                "text": self.text,
                "score": self.score}


class UserStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_won = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)


@receiver(post_save, sender=User)
def create_user_stats(sender, instance, created, **kwargs):
    if created:
        UserStats.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_stats(sender, instance, **kwargs):
    instance.userstats.save()
