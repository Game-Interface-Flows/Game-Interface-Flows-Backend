from django.urls import path
from rest_framework.authtoken.views import ObtainAuthToken

from .views import *

urlpatterns = [
    path("flows/<pk>/", FlowViewDetail.as_view()),
    path("flows/", FlowView.as_view()),
    path("auth/signup/", CreateUserView.as_view()),
    path("auth/token/", ObtainAuthToken.as_view()),
    path("test/", TestStorageView.as_view()),
]
