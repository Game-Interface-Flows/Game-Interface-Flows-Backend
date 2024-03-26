from rest_framework import status
from rest_framework.generics import *
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.interface_flows_api.serializers import *
from apps.interface_flows_api.services.auth_service import AuthService
from apps.interface_flows_api.services.flow_service import FlowService


class FlowView(APIView):
    service = FlowService()

    def get(self, *args, **kwargs):
        sort_param = self.request.GET.get("sort", "date")
        order_param = self.request.GET.get("order", "DESC")
        limit_param = int(self.request.GET.get("limit", 10))
        offset_param = int(self.request.GET.get("offset", 0))
        queryset = self.service.get_public_flows(
            sort_param, order_param, limit_param, offset_param
        )
        serializer = FlowSimpleSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        flow = self.service.create_new_flow(request.FILES.getlist("frames"))
        serializer = FlowSerializer(flow)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FlowViewDetail(RetrieveAPIView):
    serializer_class = FlowSerializer
    service = FlowService()
    queryset = service.get_public_flows()

    def get(self, request, *args, **kwargs):
        user = request.user
        id = self.kwargs["pk"]
        flow = self.service.get_flow_by_id(flow_id=id, user=user)
        if flow is None:
            return Response({"status": "details"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(flow)
        return Response(serializer.data)


class CreateUserView(CreateAPIView):
    serializer_class = UserSerializer
    service = AuthService()

    def post(self, request, *args, **kwargs):
        username = request.data["username"]
        password = request.data["password"]
        email = request.data["email"]
        user = self.service.create_user(username, password, email=email)
        serializer = self.serializer_class(user)
        return Response(serializer.data)


class TestStorageView(CreateAPIView):
    serializer_class = FrameSerializer
    queryset = Frame.objects.all()
