from django import forms


class PostForm(forms.Form):
    text = forms.CharField(label="Text", max_length=140)


class UsernameForm(forms.Form):
    username = forms.CharField(label="Add follow", max_length=20, strip=True, min_length=3)
