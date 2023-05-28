# Generated by Django 4.2.1 on 2023-05-16 02:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("my_app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserStatus",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("online", models.BooleanField(default=False)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
