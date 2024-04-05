from django.contrib import admin

from apps.interface_flows_api.models import (Comment, Connection, Flow, Genre,
                                             Like, Platform, Profile, Screen,
                                             ScreenVisualProperties)

admin.site.register(
    [
        Profile,
        Flow,
        Screen,
        Connection,
        Comment,
        Like,
        Genre,
        Platform,
        ScreenVisualProperties,
    ]
)
