# Generated by Django 4.0.3 on 2024-02-09 00:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0006_gameplayer_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='round',
            name='multiplier',
            field=models.FloatField(default=1),
        ),
    ]
