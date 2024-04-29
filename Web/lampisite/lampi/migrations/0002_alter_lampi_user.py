# Generated by Django 4.0.2 on 2022-02-19 21:20

from django.conf import settings
from django.db import migrations, models
import lampi.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lampi', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lampi',
            name='user',
            field=models.ForeignKey(on_delete=models.SET(lampi.models.get_parked_user), to=settings.AUTH_USER_MODEL),  # noqa
        ),
    ]
