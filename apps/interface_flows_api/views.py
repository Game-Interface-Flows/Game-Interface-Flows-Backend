from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import NotFound, ParseError, PermissionDenied
from rest_framework.generics import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.interface_flows_api.exceptions import (
    MLServicesException, MLServicesUnavailableException, MLServiceUnavailable,
    PrivateFlowException, UnverifiedFlowExists, UnverifiedFlowExistsException,
    VideoProcessing, VideoProcessingException)
from apps.interface_flows_api.selectors.flow_selector import flow_selector
from apps.interface_flows_api.serializers import *
from apps.interface_flows_api.services.auth_service import auth_service
from apps.interface_flows_api.services.flow_build_service import \
    flow_build_service
from apps.interface_flows_api.services.flow_social_service import \
    flow_social_service


class FlowView(APIView):
    """Controller to create a new flow or get list of views."""

    class FlowsPagination(PageNumberPagination):
        """Simple flows pagination for listing."""

        page_size = 10
        page_size_query_param = "page_size"
        max_page_size = 10

    pagination_class = FlowsPagination
    object_name = "flow"

    def get_permissions(self):
        if self.request.method == "POST":
            self.authentication_classes = [TokenAuthentication]
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def get(self, request, *args, **kwargs):
        sort_param = request.query_params.get("sort", "date")
        order_param = request.query_params.get("order", "desc")
        genres = request.query_params.getlist("genre", None)
        platforms = request.query_params.getlist("platform", None)

        flows = flow_selector.get_public_flows(
            sort_param, order_param, genres, platforms
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(flows, request, view=self)
        if page is not None:
            serializer = FlowSimpleSerializer(
                page, many=True, context={"request": self.request}
            )
            return paginator.get_paginated_response(serializer.data)
        serializer = FlowSimpleSerializer(
            flows, many=True, context={"request": self.request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # check video and its extensions
        if "video" not in request.FILES:
            raise ParseError(detail="Video is required to create a flow.", code=400)
        video_file = request.FILES["video"]
        allowed_extensions = ["mp4", "avi", "mov"]
        file_extension = video_file.name.split(".")[-1].lower()
        if file_extension not in allowed_extensions:
            raise ParseError(
                detail="Invalid file format. Supported formats are: .mp4, .avi, .mov",
                code=400,
            )

        user = request.user
        platforms = request.data.getlist("platforms", None)
        genres = request.data.getlist("genres", None)
        interval = int(request.data.get("interval", 3))

        serializer = FlowSimpleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            flow = flow_build_service.create_new_flow(
                **serializer.validated_data,
                video_file=video_file,
                user=user,
                interval=interval,
                platforms=platforms,
                genres=genres,
            )
            serializer = FlowSerializer(flow, context={"request": self.request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except UnverifiedFlowExistsException:
            raise UnverifiedFlowExists()
        except VideoProcessingException:
            raise VideoProcessing()
        except MLServicesUnavailableException:
            raise MLServiceUnavailable()
        except MLServicesException:
            raise MLServiceUnavailable()


class MyFlowView(ListAPIView):
    """Controller to get flows created by a user."""

    serializer_class = FlowSimpleSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return flow_selector.get_my_flows(user)


class LikedFlowView(ListAPIView):
    """Controller to get flows liked by a user."""

    serializer_class = FlowSimpleSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return flow_selector.get_liked_flows(user)


class FlowVisibilityMixin:
    """Mixin to check if a user has rights to view a flow."""

    @staticmethod
    def get_flow(flow_id, user):
        try:
            return flow_selector.get_flow_by_id(flow_id=flow_id, user=user)
        except ObjectDoesNotExist:
            raise NotFound(detail=f"Flow with id={flow_id} not found.", code=404)
        except PrivateFlowException:
            raise PermissionDenied(detail="Access to the flow is denied.", code=403)


class FlowDetailView(RetrieveAPIView, FlowVisibilityMixin):
    """Controller to retrieve a detailed flow."""

    serializer_class = FlowSerializer
    queryset = flow_selector.get_public_flows()

    def get_object(self):
        user = self.request.user
        flow = self.get_flow(self.kwargs["pk"], user)
        return flow


class FlowLikeView(APIView, FlowVisibilityMixin):
    """Controller to like or dislike a flow."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_flow_for_user(self, request, pk):
        return self.get_flow(pk, request.user)

    def post(self, request, *args, **kwargs):
        flow = self.get_flow_for_user(request, self.kwargs["pk"])
        flow = flow_social_service.like_flow(flow=flow, user=request.user)
        serializer = LikesSerializer(flow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        flow = self.get_flow_for_user(request, self.kwargs["pk"])
        try:
            flow = flow_social_service.like_flow(
                flow=flow, user=request.user, like=False
            )
        except ObjectDoesNotExist:
            raise NotFound(detail=f"Like must be set before dislike.", code=404)
        serializer = LikesSerializer(flow)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FlowCommentView(APIView, FlowVisibilityMixin):
    """Controller to create a new comment"""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer

    def post(self, request, *args, **kwargs):
        user = self.request.user
        flow = self.get_flow(self.kwargs["pk"], user)

        data = request.data.copy()
        data["flow"] = flow.id
        data["author"] = user.profile

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)

        flow_social_service.comment_flow(flow, user, data["text"])

        return Response(status=status.HTTP_201_CREATED)


class CreateUserView(CreateAPIView):
    """Controller to create a new user"""

    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        auth_service.create_user(**serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GenresView(ListAPIView):
    """Controller to retrieve all genres"""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class PlatformsView(ListAPIView):
    """Controller to retrieve all platforms"""

    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer


class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception:
            custom_response = {"details": "Unable to log in with provided credentials."}
            return Response(custom_response, status=status.HTTP_400_BAD_REQUEST)
