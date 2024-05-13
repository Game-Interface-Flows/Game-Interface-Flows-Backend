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


class GenreSerializer(ModelSerializer):
    class Meta:
        model = Genre
        fields = "__all__"


class PlatformSerializer(ModelSerializer):
    class Meta:
        model = Platform
        fields = "__all__"


class FlowBaseSerializer(ModelSerializer):
    total_likes = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    genres = GenreSerializer(many=True, read_only=True)
    platforms = PlatformSerializer(many=True, read_only=True)
    status = serializers.CharField(source="get_status_display", read_only=True)
    process = serializers.CharField(source="get_process_display", read_only=True)
    visibility = serializers.CharField(source="get_visibility_display", read_only=True)

    class Meta:
        model = Flow
        fields = [
            "id",
            "title",
            "date",
            "total_likes",
            "genres",
            "platforms",
            "is_liked",
            "process",
            "status",
            "visibility",
        ]

    def get_is_liked(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.likes.filter(user=user.profile).exists()
        return False


class FlowSimpleSerializer(FlowBaseSerializer):
    class Meta(FlowBaseSerializer.Meta):
        fields = FlowBaseSerializer.Meta.fields + ["flow_thumbnail_url"]


class FlowSerializer(FlowBaseSerializer):
    total_screens = serializers.ReadOnlyField()
    average_connectivity = serializers.ReadOnlyField()
    max_x = serializers.ReadOnlyField()
    max_y = serializers.ReadOnlyField()
    screens = ScreenSerializer(read_only=True, many=True)
    comments = CommentSerializer(read_only=True, many=True)
    author = ProfileSerializer(read_only=True)
    screens_properties = ScreenVisualPropertiesSerializer(read_only=True)

    class Meta(FlowBaseSerializer.Meta):
        fields = FlowBaseSerializer.Meta.fields + [
            "total_screens",
            "average_connectivity",
            "max_x",
            "max_y",
            "screens",
            "comments",
            "author",
            "screens_properties",
        ]


class LikesSerializer(ModelSerializer):
    total_likes = serializers.ReadOnlyField()

    class Meta:
        model = Flow
        fields = ["total_likes"]
