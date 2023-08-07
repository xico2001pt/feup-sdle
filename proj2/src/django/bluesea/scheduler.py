import threading
import time
import sched
from loguru import logger
from datetime import timedelta
from django.conf import settings
from .models import Post, Author, BlueseaUser
from .communication import kademlia_set_followers, fetch_posts_from_author
from .utils import get_datetime


class Scheduler(threading.Thread): 
    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        self.s = sched.scheduler(time.time, time.sleep)


    def update_posts_job(self):
        logger.debug("Fetching posts")

        usernames = [user.user.username for user in BlueseaUser.objects.all()]
        authors = [author for author in Author.objects.all() if author.username not in usernames]

        for author in authors:
            fetch_posts_from_author(author)
                        
        self.s.enter(settings.FETCH_POSTS_INTERVAL, 1, self.update_posts_job, ())
    

    def update_followers_job(self):
        logger.debug("Updating followers")
        for bluesea_user in BlueseaUser.objects.all():
            followers = bluesea_user.followers.order_by('-last_update')[:15]
            followers_addresses = [f"{f.ip}:{f.port}" for f in followers]
            kademlia_set_followers(bluesea_user.user.username, followers_addresses)
        self.s.enter(settings.UPDATE_FOLLOWERS_INTERVAL, 1, self.update_followers_job, ())


    def posts_garbage_collection_job(self):
        logger.debug("Running posts garbage collection")

        usernames = [user.user.username for user in BlueseaUser.objects.all()]
        posts = Post.objects.exclude(author__username__in=usernames)

        minimum_datetime = get_datetime() - timedelta(seconds=settings.POST_TTL)
        posts.filter(date__lt=minimum_datetime).delete()
        self.s.enter(settings.GARBAGE_COLLECTION_INTERVAL, 2, self.posts_garbage_collection_job, ())
    
    
    def author_garbage_collection_job(self):
        logger.debug("Running author garbage collection")
        user_authors = set([user.user.username for user in BlueseaUser.objects.all()])
        active_authors = set([author.username for user in BlueseaUser.objects.all() for author in user.following.all()])
        active_authors = active_authors.union(user_authors)
        
        inactive_authors = Author.objects.exclude(username__in=active_authors)
        inactive_authors.delete()
        self.s.enter(settings.GARBAGE_COLLECTION_INTERVAL, 2, self.author_garbage_collection_job, ())


    def run(self):
        logger.info("Initiated scheduler")
        self.s.enter(settings.FETCH_POSTS_INTERVAL, 1, self.update_posts_job, ())
        self.s.enter(settings.UPDATE_FOLLOWERS_INTERVAL, 1, self.update_followers_job, ())
        self.s.enter(settings.GARBAGE_COLLECTION_INTERVAL, 2, self.posts_garbage_collection_job, ())
        self.s.enter(settings.GARBAGE_COLLECTION_INTERVAL, 2, self.author_garbage_collection_job, ())
        self.s.run()