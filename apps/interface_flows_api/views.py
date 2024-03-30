from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.interface_flows_api.exceptions import (
    MLServicesUnavailableException, PrivateFlowException)
from apps.interface_flows_api.serializers import *
from apps.interface_flows_api.services.auth_service import AuthService
from apps.interface_flows_api.services.flow_service import FlowService


class FlowView(APIView):
    service = FlowService()

    def get_permissions(self):
        if self.request.method == "POST":
            self.authentication_classes = [TokenAuthentication]
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def get(self, request):
        sort_param = self.request.GET.get("sort", "date")
        order_param = self.request.GET.get("order", "DESC")
        limit_param = int(self.request.GET.get("limit", 10))
        offset_param = int(self.request.GET.get("offset", 0))

        flows = self.service.get_public_flows(
            sort_param, order_param, limit_param, offset_param
        )
        serializer = FlowSimpleSerializer(flows, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        user = request.user
        frames = request.FILES.getlist("frames")
        if frames is None:
            return Response()
        try:
            flow = self.service.create_new_flow(frames=frames, user=user)
            serializer = FlowSerializer(flow)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except MLServicesUnavailableException as e:
            return Response(
                {"error": "Failed to create flow", "message": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            return Response(
                {"error": "Failed to create flow", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class FlowDetailView(RetrieveAPIView):
    serializer_class = FlowSerializer
    service = FlowService()
    queryset = service.get_public_flows()

    def get(self, request, *args, **kwargs):
        user = request.user
        id = self.kwargs["pk"]
        try:
            flow = self.service.get_flow_by_id(flow_id=id, user=user)
            serializer = self.serializer_class(flow)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(
                {
                    "error": "Failed to get flow",
                    "message": f"Flow with id={id} not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except PrivateFlowException:
            return Response(
                {
                    "error": "Failed to get flow",
                    "message": f"You do not have rights to access this flow.",
                },
                status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION,
            )
        except Exception as e:
            return Response(
                {"error": "Failed to get flow", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CreateUserView(CreateAPIView):
    serializer_class = UserSerializer
    service = AuthService()

    def post(self, request, *args, **kwargs):
        username = request.data["username"]
        password = request.data["password"]
        email = request.data["email"]
        user = self.service.create_user(username, password, email=email)
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
