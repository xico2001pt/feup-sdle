from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from .utils import get_datetime


class Author(models.Model):
    username = models.TextField(max_length=20)
    ip = models.TextField(max_length=45) 
    port = models.IntegerField()
    last_update = models.DateTimeField(default=get_datetime)


class BlueseaUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="bluesea_user")
    following = models.ManyToManyField(Author)


@receiver(post_save, sender=User)
def create_bluesea_user(sender, instance, created, **kwargs):
    if created:
        BlueseaUser.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_bluesea_user(sender, instance, **kwargs):
    instance.bluesea_user.save()


class Follower(models.Model):
    ip = models.TextField(max_length=45) 
    port = models.IntegerField()
    last_update = models.DateTimeField(default=get_datetime)
    followed_user = models.ForeignKey(BlueseaUser, on_delete=models.CASCADE, related_name="followers")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ip", "port", "followed_user"], name="follower_unique_constraint"
            )
        ]


class Post(models.Model):
    identifier = models.IntegerField(null=True)
    text = models.TextField(max_length=140)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    date = models.DateTimeField(default=get_datetime)
    signature = models.TextField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["identifier", "author"], name="unique_constraint"
            )
        ]
        ordering = ["-date"]