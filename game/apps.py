import os

from django.apps import AppConfig

from game.selenium_trends import SeleniumTrends


class GameConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'game'

    def ready(self):
        if os.environ.get('RUN_MAIN'):
            SeleniumTrends().setup()
