from django.urls import path

from apps.interface_flows_api.views import *

urlpatterns = [
    path("genres/", GenresView.as_view(), name="genres"),
    path("platforms/", PlatformsView.as_view(), name="platforms"),
    path("flows/", FlowView.as_view(), name="flows"),
    path("flows/liked/", LikedFlowView.as_view(), name="liked_flows"),
    path("flows/my/", MyFlowView.as_view(), name="my_flows"),
    path("flows/<int:pk>/", FlowDetailView.as_view(), name="flow"),
    path("flows/<int:pk>/likes/", FlowLikeView.as_view(), name="likes"),
    path("flows/<int:pk>/comments/", FlowCommentView.as_view(), name="comments"),
    path("auth/signup/", CreateUserView.as_view(), name="signup"),
    path("auth/token/", CustomObtainAuthToken.as_view(), name="login"),
]
