from apps.interface_flows_api.models import Profile, User
from apps.interface_flows_api.repositories.repository import IRepository


class UserRepository(IRepository):
    @staticmethod
    def create_new_user(username: str, password: str, email: str) -> User:
        user = User.objects.create_user(username=username, email=email)
        user.set_password(password)
        user.save()
        return user

    @staticmethod
    def get_profile_by_user(user: User) -> Profile | None:
        if user.id is None:
            return None
        return Profile.objects.get(user=user)


user_repository = UserRepository()
