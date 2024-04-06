from django.core.exceptions import ObjectDoesNotExist

from apps.interface_flows_api.models import Profile, User
from apps.interface_flows_api.repositories.user_repository import (
    UserRepository, user_repository)


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, username, password, email) -> User:
        return self.repository.create_new_user(username, password, email)

    def get_profile(self, user) -> Profile:
        try:
            return self.repository.get_profile_by_user(user)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist


auth_service = AuthService(user_repository)
