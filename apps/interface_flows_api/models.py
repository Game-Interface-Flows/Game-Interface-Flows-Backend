from django.contrib.auth.models import User
from django.db import models
from django.db.models import (BooleanField, CharField, DateField, ForeignKey,
                              ImageField, IntegerField, ManyToManyField, Model,
                              OneToOneField, TextChoices, TextField)
from django.utils.translation import gettext_lazy as _

import apps.interface_flows_api.config as config


class Profile(Model):
    user = OneToOneField(
        User, on_delete=models.CASCADE, null=False, blank=False, related_name="profile"
    )
    profile_photo_url = ImageField(
        upload_to=config.AWS_FOLDER_PROFILES,
        default=f"{config.AWS_FOLDER_PROFILES}/{config.DEFAULT_PROFILE}",
    )

    def __str__(self):
        return self.user.username


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
    VERIFIED = "VR", _("Verified")
    ON_MODERATION = "MD", _("Moderation")


class FlowVisibility(TextChoices):
    PUBLIC = "PB", _("Public")
    PRIVATE = "PV", _("Private")


class ScreenVisualProperties(Model):
    width = IntegerField(default=480)
    height = IntegerField(default=270)

    class Meta:
        unique_together = (
            "width",
            "height",
        )

    def __str__(self):
        return f"{self.width}x{self.height}"

    @property
    def offset_x(self) -> int:
        width_ratio = 0.2
        width = self.width
        return round(int(width) * width_ratio)

    @property
    def offset_y(self) -> int:
        height_ratio = 0.15
        height = self.height
        return round(int(height) * height_ratio)


class Flow(Model):
    title = TextField()
    description = TextField(null=True, blank=True)
    status = CharField(
        max_length=2,
        choices=FlowStatus.choices,
        default=FlowStatus.ON_MODERATION,
    )
    visibility = CharField(
        max_length=2, choices=FlowVisibility.choices, default=FlowVisibility.PUBLIC
    )
    author = ForeignKey(
        Profile, on_delete=models.CASCADE, null=False, related_name="user_flows"
    )
    date = DateField(auto_now=False, auto_now_add=True)
    flow_thumbnail_url = ImageField(
        upload_to=config.AWS_FOLDER_THUMBNAILS,
        default=f"{config.AWS_FOLDER_THUMBNAILS}/{config.DEFAULT_THUMBNAIL}",
    )
    genres = ManyToManyField(Genre, related_name="genres", blank=True)
    platforms = ManyToManyField(Platform, related_name="platforms", blank=True)
    screens_properties = ForeignKey(
        ScreenVisualProperties,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flows_visual_properties",
    )

    @property
    def total_likes(self) -> int:
        return len(Like.objects.filter(flow=self))

    def __str__(self):
        return f"{self.title} ({self.id})"


class Screen(Model):
    flow = ForeignKey(
        Flow, on_delete=models.CASCADE, null=False, related_name="screens"
    )
    flow_screen_number = IntegerField()
    image = ImageField(
        upload_to=config.AWS_FOLDER_SCREENS,
        default=f"{config.AWS_FOLDER_SCREENS}/{config.DEFAULT_SCREEN}",
    )
    position_x = IntegerField(default=0)
    position_y = IntegerField(default=0)

    class Meta:
        unique_together = (
            "flow",
            "flow_screen_number",
        )
        ordering = ["position_y", "position_x"]


class Anchors(TextChoices):
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


class Connection(Model):
    bidirectional = BooleanField(default=False)
    screen_out = ForeignKey(
        Screen, on_delete=models.CASCADE, null=False, related_name="connections_out"
    )
    screen_in = ForeignKey(
        Screen, on_delete=models.CASCADE, null=False, related_name="connections_in"
    )

    @property
    def source_anchor(self) -> Anchors:
        """Source anchor should be on right or bottom side."""
        if (
            self.screen_out.position_y < self.screen_in.position_y
            and self.screen_out.position_x >= self.screen_in.position_x
        ):
            return Anchors.BOTTOM
        return Anchors.RIGHT

    @property
    def target_anchor(self) -> Anchors:
        """Target anchor should be on top or left side."""
        if (
            self.screen_in.position_y > self.screen_out.position_y
            and self.screen_in.position_x <= self.screen_out.position_x
        ):
            return Anchors.TOP
        return Anchors.LEFT

    class Meta:
        unique_together = (
            "screen_out",
            "screen_in",
        )


class Comment(Model):
    author = ForeignKey(
        Profile, on_delete=models.CASCADE, null=False, related_name="comments"
    )
    flow = ForeignKey(
        Flow, on_delete=models.CASCADE, null=False, related_name="commented_by"
    )
    text = TextField(max_length=240)


class Like(Model):
    user = ForeignKey(
        Profile, on_delete=models.CASCADE, null=False, related_name="likes"
    )
    flow = ForeignKey(
        Flow, on_delete=models.CASCADE, null=False, related_name="liked_by"
    )

    class Meta:
        unique_together = (
            "user",
            "flow",
        )
