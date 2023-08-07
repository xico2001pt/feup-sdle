import os
import sys
import zmq
import requests
from datetime import datetime
from django.conf import settings
from django.db.models import Max
from loguru import logger
from .crypto import get_public_key, import_key_from_string, key_from_string, verify_signature
from .models import Post


def kademlia_send(json):
    port = os.getenv("BLUESEA_PORT")
    context = zmq.Context()
    client = context.socket(zmq.REQ)
    logger.debug("Connecting to kademlia")
    client.connect(f"ipc:///tmp/kademlia/{port}")
    logger.debug("Sending message to kademlia")
    client.send_json(json)
    response = client.recv_json()
    logger.debug(f"Message received from kademlia: {response}")
    return response


def kademlia_get(username):
    return kademlia_send({
        "op": "GET", 
        "body": {
            "key": username
        }
    })


def kademlia_set_followers(username, followers):
    return kademlia_send({
        "op": "SET_FOLLOWERS",
        "body": {
            "username": username,
            "followers": followers
        }
    })


def kademlia_set_last_post_timestamp(username, timestamp):
    return kademlia_send({
        "op": "SET_LAST_POST_TIMESTAMP",
        "body": {
            "username": username,
            "timestamp": timestamp
        }
    })


def kademlia_register(username, ip, port):
    return kademlia_send({
        "op": "REGISTER",
        "body": {
            "username": username,
            "ip": ip,
            "port": port,
            "followers": [],
            "public_key": get_public_key().export_key().decode("utf-8")
        }
    })


def fetch_posts_from_author(author):
    author_content = kademlia_get(author.username)
    status = author_content.get("status", None)
    if not status or status == "NACK":
        return False

    body = author_content.get("body", None)
    if not body:
        return False

    last_post_timestamp = body.get("last_post_timestamp", None)
    if not last_post_timestamp:
        return False
    
    last_post_timestamp_locally = Post.objects.filter(author=author).aggregate(Max('date')).get("date__max", None)
    if last_post_timestamp_locally and last_post_timestamp_locally >= datetime.fromisoformat(last_post_timestamp):
        # There's no need to update the posts, since they're up to date.
        logger.debug(f"skipping updating posts for {author.username}, they're already up to date")
        return False

    public_key = body.get("public_key", None)
    if not public_key:
        return False

    public_key = import_key_from_string(public_key)

    port = int(sys.argv[-1].split(':')[1])

    posts = []
    try:
        data = requests.get(f'http://{author.ip}:{author.port}/api/{author.username}/posts?port={port}').json()
        status = data.get("status", None)
        if status and status == "ACK":
            posts = data.get("data", None)
            if posts == None:
                logger.debug(f"Received incorrect /posts API message format from author {author.username}")
                return False
        else:
            posts = fetch_posts_from_followers(author.username) # If NACK received from original node fetch posts from followers
    except requests.exceptions.RequestException:
        posts = fetch_posts_from_followers(author.username)

    if posts:
        for post in posts:
            if verify_signature(public_key, post["text"], key_from_string(post["signature"])):
                Post.objects.update_or_create(
                    identifier=post["identifier"],
                    text=post["text"],
                    date=datetime.fromisoformat(post["date"]),
                    signature=post["signature"],
                    author=author
                )


def fetch_posts_from_followers(username):
    logger.debug(f"{username} seems to be offline (or an error has occured), fetching posts from followers")

    response = kademlia_get(username)
    status = response.get("status", None)
    if not status or status == "NACK":
        logger.debug(f"Can't find user with username {username}")
        return None

    body = response.get("body", None)
    if not body:
        return None

    followers_servers = body.get("followers", None)
    if followers_servers == None:
        return None

    for follower_server in followers_servers:
        ip, port = follower_server.split(":")
        
        logger.debug(f"Trying to contact {ip} and {port}")
        
        try:
            data = requests.get(f'http://{ip}:{port}/api/{username}/posts')
        except requests.exceptions.RequestException: 
            continue
            
        if data.ok:
            if settings.CACHE_OFFLINE_FOLLOWERS:
                update_followers_of_offline_node(username, followers_servers)
            return data.json()['data']

    return None


def get_ip_port():
    port = int(sys.argv[-1].split(':')[1])
    if settings.DEBUG:
        return "127.0.0.1", port
    else:
        response = requests.get('https://api64.ipify.org?format=json').json()
        return response["ip"], port


def update_followers_of_offline_node(username, followers_servers):
    ip, port = get_ip_port()
    ip_port = f"{ip}:{port}"
    if ip_port not in followers_servers:
        logger.info(f"Adding {ip_port} to {username}'s followers, since this node seems to be offline.")
        followers_servers.insert(0, ip_port)
        kademlia_set_followers(username, followers_servers)
