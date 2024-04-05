from django.contrib.auth.models import User
from django.db import models
from django.db.models import (BooleanField, CharField, DateField, ForeignKey,
                              ImageField, IntegerField, ManyToManyField, Model,
                              OneToOneField, TextChoices, TextField)

import apps.interface_flows_api.config as config


class Profile(Model):
    user = OneToOneField(
        User, on_delete=models.CASCADE, null=False, blank=False, related_name="profile"
    )
    profile_photo_url = ImageField(
        upload_to=config.AWS_FOLDER_PROFILES,
        default=f"{config.AWS_FOLDER_PROFILES}/{config.DEFAULT_PROFILE_PIC}",
    )


class Platform(Model):
    name = TextField(max_length=64, unique=True)
    platform_icon_url = ImageField(
        upload_to=config.AWS_FOLDER_ICONS,
        default=f"{config.AWS_FOLDER_ICONS}/{config.DEFAULT_ICON}",
    )

    def __str__(self):
        return self.name


class Genre(Model):
    name = TextField(max_length=64, unique=True)
    genre_icon_url = ImageField(
        upload_to=config.AWS_FOLDER_ICONS,
        default=f"{config.AWS_FOLDER_ICONS}/{config.DEFAULT_ICON}",
    )

    def __str__(self):
        return self.name


class FlowStatus(TextChoices):
    VERIFIED = ("VR",)
    ON_MODERATION = "MD"


class FlowVisibility(TextChoices):
    PUBLIC = ("PB",)
    PRIVATE = "PV"


class ScreenVisualProperties(Model):
    width = IntegerField(default=480)
    height = IntegerField(default=270)

    class Meta:
        unique_together = (
            "width",
            "height",
        )

    @property
    def offset_x(self):
        width = self.width.value_to_string(self)
        return round(int(width) * config.WIDTH_RATIO)

    @property
    def offset_y(self):
        height = self.height.value_to_string(self)
        return round(int(height) * config.HEIGHT_RATIO)


class Flow(Model):
    title = TextField()
    description = TextField()
    status = CharField(
        max_length=2,
        choices=FlowStatus.choices,
        default=FlowStatus.ON_MODERATION,
    )
    visibility = CharField(
        max_length=2, choices=FlowVisibility.choices, default=FlowVisibility.PUBLIC
    )
    author = ForeignKey(
        Profile, on_delete=models.CASCADE, null=False, related_name="flows"
    )
    date = DateField(auto_now=False, auto_now_add=True)
    flow_thumbnail_url = ImageField(
        upload_to=config.AWS_FOLDER_THUMBNAILS,
        default=f"{config.AWS_FOLDER_THUMBNAILS}/{config.DEFAULT_FLOW_THUMBNAIL}",
    )
    genres = ManyToManyField(Genre, related_name="genres", blank=True)
    platforms = ManyToManyField(Platform, related_name="platforms", blank=True)
    screens_properties = ForeignKey(
        ScreenVisualProperties,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flows",
    )

    @property
    def total_likes(self) -> int:
        return len(Like.objects.filter(flow=self))

    @property
    def is_public_and_verified(self):
        return (
            self.visibility == FlowVisibility.PUBLIC
            and self.status == FlowStatus.VERIFIED
        )

    def __str__(self):
        return self.title


class Screen(Model):
    flow = ForeignKey(
        Flow, on_delete=models.CASCADE, null=False, related_name="screens"
    )
    flow_screen_number = IntegerField()
    image = ImageField(upload_to=config.AWS_FOLDER_SCREENS)
    position_x = IntegerField(default=0)
    position_y = IntegerField(default=0)

    class Meta:
        unique_together = (
            "flow",
            "flow_screen_number",
        )
        ordering = ["position_y", "position_x"]


class Anchors(TextChoices):
    LEFT = ("left",)
    RIGHT = ("right",)
    TOP = ("top",)
    BOTTOM = ("bottom",)


class Connection(Model):
    bidirectional = BooleanField(default=False)
    screen_out = ForeignKey(
        Screen, on_delete=models.CASCADE, null=False, related_name="connections_out"
    )
    screen_in = ForeignKey(
        Screen, on_delete=models.CASCADE, null=False, related_name="connections_in"
    )

    @property
    def target_anchor(self):
        return Anchors.TOP

    @property
    def source_anchor(self):
        return Anchors.TOP

    class Meta:
        unique_together = (
            "screen_out",
            "screen_in",
        )


class Comment(Model):
    author = ForeignKey(
        Profile, on_delete=models.CASCADE, null=False, related_name="user_comments"
    )
    flow = ForeignKey(
        Flow, on_delete=models.CASCADE, null=False, related_name="flow_comments"
    )
    text = TextField(max_length=240)


class Like(Model):
    user = ForeignKey(
        Profile, on_delete=models.CASCADE, null=False, related_name="user_like"
    )
    flow = ForeignKey(
        Flow, on_delete=models.CASCADE, null=False, related_name="flow_like"
    )

    class Meta:
        unique_together = (
            "user",
            "flow",
        )
