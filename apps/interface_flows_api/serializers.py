from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from .models import *


class ProfileSerializer(ModelSerializer):
    username = serializers.CharField(source="user.username")

    class Meta:
        model = Profile
        exclude = ["user"]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "password", "email"]


class ConnectionSerializer(ModelSerializer):
    target_anchor = serializers.ReadOnlyField()
    source_anchor = serializers.ReadOnlyField()

    class Meta:
        model = Connection
        fields = "__all__"


class FrameSerializer(ModelSerializer):
    image_out = ConnectionSerializer(read_only=True, many=True)

    class Meta:
        model = Frame
        fields = ["id", "frame", "position_x", "position_y", "image_out"]


class CommentSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "text", "author"]


class FlowSimpleSerializer(ModelSerializer):
    total_likes = serializers.ReadOnlyField()
    author = ProfileSerializer(write_only=True)

    class Meta:
        model = Flow
        fields = ["id", "title", "date", "total_likes", "flow_thumbnail_url", "author"]


class FlowSerializer(ModelSerializer):
    total_likes = serializers.ReadOnlyField()
    frames = FrameSerializer(read_only=True, many=True)
    flow_comments = CommentSerializer(read_only=True, many=True)
    author = ProfileSerializer(read_only=True)

    class Meta:
        model = Flow
        exclude = ["flow_thumbnail_url"]
