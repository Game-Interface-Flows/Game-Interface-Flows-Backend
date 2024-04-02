from django.urls import path
from rest_framework.authtoken.views import ObtainAuthToken

from .views import *

urlpatterns = [
    path("genres/", GenresView.as_view()),
    path("platforms", PlatformsView.as_view()),
    path("flows/", FlowView.as_view()),
    path("flows/<pk>/", FlowDetailView.as_view()),
    path("flows/<pk>/likes/", FlowLikeView.as_view()),
    path("flows/<pk>/comments/", FlowCommentView.as_view()),
    path("auth/signup/", CreateUserView.as_view()),
    path("auth/token/", ObtainAuthToken.as_view()),
]
