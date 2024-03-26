from django.contrib import admin

from .models import Connection, Flow, Frame, Profile

admin.site.register([Profile, Flow, Frame, Connection])
