from django.contrib import admin

from .models import (Comment, Connection, Flow, Screen, Genre, Like, Platform,
                     Profile)

admin.site.register([Profile, Flow, Screen, Connection, Comment, Like, Genre, Platform])
