from apps.interface_flows_api.repositories.user_repository import \
    user_repository


class AuthService:
    def __init__(self, repository):
        self.repository = repository

    def create_user(self, username, password, email):
        return self.repository.create_new_user(username, password, email)

    def get_all_users(self):
        return self.repository.get_all_users()

    def get_profile(self, user):
        return self.repository.get_profile_by_user(user)


auth_service = AuthService(user_repository)
