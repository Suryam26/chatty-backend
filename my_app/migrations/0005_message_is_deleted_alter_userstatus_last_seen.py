# Generated by Django 4.2.1 on 2023-05-18 13:48

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("my_app", "0004_alter_userstatus_last_seen"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="userstatus",
            name="last_seen",
            field=models.DateTimeField(
                default=datetime.datetime(2023, 5, 18, 13, 48, 20, 173746)
            ),
        ),
    ]
