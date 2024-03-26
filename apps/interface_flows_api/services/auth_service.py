from apps.interface_flows_api.repositories.user_repository import \
    UserRepository


class AuthService:
    repository = UserRepository()

    def create_user(self, username, password, email):
        return self.repository.create_new_user(username, password, email)

    def get_all_users(self):
        return self.repository.get_all_users()

    def get_profile(self, user):
        return self.repository.get_profile_by_user(user)
