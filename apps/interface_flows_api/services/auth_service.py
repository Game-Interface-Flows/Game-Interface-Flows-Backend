from apps.interface_flows_api.models import User


class AuthService:
    @staticmethod
    def create_user(username: str, password: str, email: str) -> User:
        user = User.objects.create_user(username=username, email=email)
        user.set_password(password)
        user.save()
        return user


auth_service = AuthService()
