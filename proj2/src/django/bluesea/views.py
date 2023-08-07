from loguru import logger
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.generic import View
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .models import Author, Post, BlueseaUser, Follower
from .forms import PostForm, UsernameForm
from .communication import kademlia_get, kademlia_register, fetch_posts_from_author, kademlia_set_last_post_timestamp
from .crypto import sign_string, key_to_string
from .utils import get_datetime


class HomePageView(View):
    def get(self, request):
        if request.user.is_authenticated:
            following = BlueseaUser.objects.get(user=request.user).following.all()
            return render(request, "pages/home.html", {
                "posts": Post.objects.filter(author__in=following) | Post.objects.filter(author__username=request.user.username),
                "following": BlueseaUser.objects.get(user=request.user).following.all()
            })
        return render(request, "pages/home.html")


class PostsView(View):
    def post(self, request):
        form = PostForm(request.POST)
        if form.is_valid():
            author = Author.objects.get(username=request.user.username)
            post_text = form.cleaned_data["text"]
            post = Post.objects.create(text=post_text, author=author, signature=key_to_string(sign_string(post_text)))
            post.identifier = post.pk
            logger.debug(f"Saving post: id={post.pk} text=\"{post.text}\" by author={author.username}")
            post.save()
            kademlia_set_last_post_timestamp(request.user.username, post.date.isoformat())
            return redirect("homepage")


class PostsApiView(View):
    def get(self, request, username):
        try:
            author = Author.objects.get(username=username)
        except Author.DoesNotExist:
            return JsonResponse({
                "status": "NACK",
                "error": "username does not exist"
            }, status=404)

        port = request.GET.get("port", None)
        if port:
            self._add_follower(username, request.META["REMOTE_ADDR"], port) 

        posts = Post.objects.filter(author=author)
        response = [{
            "identifier": post.identifier,
            "text": post.text,
            "author": post.author.username,
            "date": post.date.isoformat(),
            "signature": post.signature
        } for post in posts]

        return JsonResponse({
            "status": "ACK",
            "data": response
        })


    def _add_follower(self, followed_username, follower_ip, follower_port):
        logger.debug(f"{follower_ip}:{follower_port} now follows {followed_username}")

        followed_user = User.objects.get(username=followed_username).bluesea_user
        if not followed_user:
            return
        
        follower, created = Follower.objects.get_or_create(ip=follower_ip, port=follower_port, followed_user=followed_user)
        if not created:
            follower.last_update = str(get_datetime())
            follower.save()


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("homepage")
        else:
            return render(request, "pages/form.html", {"page_title": "Register", "form": UserCreationForm()})


    def post(self, request):
        form = UserCreationForm(data=request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            response = kademlia_register(user.username, request.META["REMOTE_ADDR"], request.META["SERVER_PORT"])

            if response["status"] == "NACK":
                messages.error(request, f"Unable to register user {user.username}")
                return redirect("register")

            Author.objects.create(username=user.username, ip=request.META["REMOTE_ADDR"], port=request.META["SERVER_PORT"])

            user.save()
            login(request, user)

            return redirect("homepage")
        else:
            for errors in form.errors.as_data().values():
                for error in [' '.join(error.messages) for error in errors]:
                    messages.error(request, error)
            return redirect("register")


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("homepage")
        else:
            return render(request, "pages/form.html", {"page_title": "Login", "form": AuthenticationForm()})


    def post(self, request):
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("homepage")
        else:
            for errors in form.errors.as_data().values():
                for error in [' '.join(error.messages) for error in errors]:
                    messages.error(request, error)
            return redirect("login")


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("homepage")


class FollowUserView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("homepage")

        form = UsernameForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]

            if username == request.user.username:
                messages.info(request, "You can't follow yourself.")
                return redirect("homepage")

            response = kademlia_get(username)

            status = response.get("status", None)
            if not status or status == "NACK":
                messages.error(request, "Couldn't find user.")
                return redirect("homepage")

            body = response.get("body", None)
            if not body:
                messages.error(request, "Unable to follow the user.")
                return redirect("homepage")

            ip, port = body.get("ip", None), body.get("port", None)
            if not ip or not port:
                messages.error(request, "Unable to follow the user.")
                return redirect("homepage")

            try:
                user = BlueseaUser.objects.get(user=request.user)
            except ObjectDoesNotExist:
                messages.error(request, "Internal error, contact administrators.")
                return redirect("homepage")

            author, _ = Author.objects.get_or_create(username=username, ip=ip, port=port)

            if author not in user.following.all():
                user.following.add(author)
                user.save()

            fetch_posts_from_author(author)

            return redirect("homepage")
        else:
            messages.error(request, "Invalid username.")
            return redirect("homepage")


class UnfollowUserView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("homepage")
        
        form = UsernameForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]

            response = kademlia_get(username)

            status = response.get("status", None)
            if not status or status == "NACK":
                messages.error(request, "Couldn't find user.")
                return redirect("homepage")

            try:
                user = BlueseaUser.objects.get(user=request.user)
                author = Author.objects.get(username=username)
                user.following.remove(author)
            except ObjectDoesNotExist:
                messages.error(request, "Internal error, contact administrators.")
                return redirect("homepage")
            
            return redirect("homepage")
        else:
            messages.error(request, "Invalid username.")
            return redirect("homepage")
        