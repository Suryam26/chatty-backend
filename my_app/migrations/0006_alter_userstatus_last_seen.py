# Generated by Django 4.2.1 on 2023-05-25 12:31

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("my_app", "0005_message_is_deleted_alter_userstatus_last_seen"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userstatus",
            name="last_seen",
            field=models.DateTimeField(
                default=datetime.datetime(2023, 5, 25, 12, 31, 36, 76321)
            ),
        ),
    ]
