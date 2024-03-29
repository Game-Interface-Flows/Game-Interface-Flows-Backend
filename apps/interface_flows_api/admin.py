from django.contrib import admin

from .models import Comment, Connection, Flow, Frame, Like, Profile

admin.site.register([Profile, Flow, Frame, Connection, Comment, Like])
