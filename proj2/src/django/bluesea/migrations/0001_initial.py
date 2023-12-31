# Generated by Django 4.1.3 on 2022-12-11 18:19

import bluesea.utils
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Author",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("username", models.TextField(max_length=20)),
                ("ip", models.TextField(default="localhost", max_length=45)),
                ("port", models.IntegerField(default=8000)),
                (
                    "last_update",
                    models.DateTimeField(default=bluesea.utils.get_datetime),
                ),
            ],
        ),
        migrations.CreateModel(
            name="BlueseaUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("following", models.ManyToManyField(to="bluesea.author")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bluesea_user",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Post",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("identifier", models.IntegerField(null=True)),
                ("text", models.TextField(max_length=140)),
                ("date", models.DateTimeField(default=bluesea.utils.get_datetime)),
                ("signature", models.TextField(null=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="bluesea.author"
                    ),
                ),
            ],
            options={
                "ordering": ["-date"],
            },
        ),
        migrations.CreateModel(
            name="Follower",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("ip", models.TextField(max_length=45)),
                ("port", models.IntegerField()),
                (
                    "last_update",
                    models.DateTimeField(default=bluesea.utils.get_datetime),
                ),
                (
                    "followed_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="followers",
                        to="bluesea.blueseauser",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="post",
            constraint=models.UniqueConstraint(
                fields=("identifier", "author"), name="unique_constraint"
            ),
        ),
        migrations.AddConstraint(
            model_name="follower",
            constraint=models.UniqueConstraint(
                fields=("ip", "port", "followed_user"),
                name="follower_unique_constraint",
            ),
        ),
    ]
