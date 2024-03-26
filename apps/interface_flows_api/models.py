from django.contrib.auth.models import User
from django.db import models
from django.db.models import (BooleanField, DateField, FloatField, ForeignKey,
                              ImageField, IntegerField, Model, OneToOneField,
                              Q, TextChoices, TextField)

import apps.interface_flows_api.config as config


class Profile(Model):
    user = OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="profile"
    )
    profile_photo_url = ImageField(
        upload_to=config.AWS_FOLDER_PROFILES,
        default=f"{config.AWS_FOLDER_PROFILES}/profile.png",
    )


class FlowStatus(TextChoices):
    VERIFIED = ("VR",)
    ON_MODERATION = "MD"


class FlowVisibility(TextChoices):
    PUBLIC = ("PB",)
    PRIVATE = "PV"


class Flow(Model):
    title = TextField()
    description = TextField()
    frames_width = IntegerField(default=480)
    frames_height = IntegerField(default=270)
    status = models.CharField(
        max_length=2,
        choices=FlowStatus.choices,
        default=FlowStatus.ON_MODERATION,
    )
    visibility = models.CharField(
        max_length=2, choices=FlowVisibility.choices, default=FlowVisibility.PUBLIC
    )
    author = ForeignKey(
        Profile, on_delete=models.CASCADE, null=True, related_name="flow_author"
    )
    date = DateField(auto_now=False, auto_now_add=True)

    @property
    def total_likes(self) -> int:
        return len(Like.objects.filter(flow=self))

    @property
    def is_public_and_verified(self):
        return (
            self.visibility == FlowVisibility.PUBLIC
            and self.status == FlowStatus.VERIFIED
        )


class Frame(Model):
    flow = ForeignKey(Flow, on_delete=models.CASCADE, null=True, related_name="frames")
    frame = ImageField(upload_to=config.AWS_FOLDER_FRAMES)
    position_x = IntegerField(default=0)
    position_y = IntegerField(default=0)

    @property
    def count_out_connections(self):
        return len(
            Connection.objects.filter(
                Q(image_out=self) | (Q(image_in=self) & Q(bidirectional=True))
            )
        )


class Anchors(TextChoices):
    LEFT = ("left",)
    RIGHT = ("right",)
    TOP = ("top",)
    BOTTOM = ("bottom",)


class Connection(Model):
    bidirectional = BooleanField(default=False)
    frame_out = ForeignKey(
        Frame, on_delete=models.CASCADE, null=False, related_name="image_out"
    )
    frame_in = ForeignKey(
        Frame, on_delete=models.CASCADE, null=False, related_name="image_in"
    )

    @property
    def target_anchor(self):
        return Anchors.TOP

    @property
    def source_anchor(self):
        if self.frame_out.position_x > 5:
            return Anchors.LEFT
        return Anchors.TOP

    class Meta:
        unique_together = (
            "frame_out",
            "frame_in",
        )


class Comment(Model):
    author = ForeignKey(
        Profile, on_delete=models.CASCADE, null=True, related_name="user_comments"
    )
    flow = ForeignKey(
        Flow, on_delete=models.CASCADE, null=True, related_name="flow_comments"
    )
    text = TextField(max_length=240)


class Like(Model):
    user = ForeignKey(
        Profile, on_delete=models.CASCADE, null=False, related_name="user_like"
    )
    flow = ForeignKey(
        Flow, on_delete=models.CASCADE, null=False, related_name="flow_like"
    )
