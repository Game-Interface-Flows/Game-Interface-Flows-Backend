from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from apps.interface_flows_api.models import *


class ProfileSerializer(ModelSerializer):
    username = serializers.CharField(source="user.username")

    class Meta:
        model = Profile
        exclude = ["user"]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "password", "email"]
        extra_kwargs = {"email": {"required": True}}


class ConnectionSerializer(ModelSerializer):
    target_anchor = serializers.ReadOnlyField()
    source_anchor = serializers.ReadOnlyField()

    class Meta:
        model = Connection
        fields = "__all__"


class ScreenVisualPropertiesSerializer(ModelSerializer):
    offset_x = serializers.ReadOnlyField()
    offset_y = serializers.ReadOnlyField()

    class Meta:
        model = ScreenVisualProperties
        fields = "__all__"


class ScreenSerializer(ModelSerializer):
    connections_out = ConnectionSerializer(read_only=True, many=True)

    class Meta:
        model = Screen
        fields = [
            "id",
            "flow_screen_number",
            "image",
            "position_x",
            "position_y",
            "connections_out",
        ]


class CommentSerializer(ModelSerializer):
    author = ProfileSerializer(read_only=True)
    flow = serializers.PrimaryKeyRelatedField(
        queryset=Flow.objects.all(), write_only=True
    )

    class Meta:
        model = Comment
        fields = "__all__"


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = "__all__"


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = "__all__"


class FlowSimpleSerializer(ModelSerializer):
    total_likes = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    genres = GenreSerializer(many=True, read_only=True)
    platforms = PlatformSerializer(many=True, read_only=True)

    class Meta:
        model = Flow
        fields = [
            "id",
            "title",
            "date",
            "total_likes",
            "flow_thumbnail_url",
            "genres",
            "platforms",
            "is_liked",
        ]

    def get_is_liked(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.likes.filter(user=user.profile).exists()
        return False


class FlowSerializer(ModelSerializer):
    total_likes = serializers.ReadOnlyField()
    screens = ScreenSerializer(read_only=True, many=True)
    comments = CommentSerializer(read_only=True, many=True)
    author = ProfileSerializer(read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    platforms = PlatformSerializer(many=True, read_only=True)
    screens_properties = ScreenVisualPropertiesSerializer(read_only=True)

    class Meta:
        model = Flow
        exclude = ["flow_thumbnail_url"]


class LikesSerializer(ModelSerializer):
    total_likes = serializers.ReadOnlyField()

    class Meta:
        model = Flow
        fields = ["total_likes"]
