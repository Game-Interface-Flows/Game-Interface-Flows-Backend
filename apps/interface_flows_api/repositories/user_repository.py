from django.contrib.auth.models import User

from apps.interface_flows_api.models import Profile


class UserRepository:
    @staticmethod
    def create_new_user(username, password, email):
        user = User.objects.create_user(username=username, email=email)
        user.set_password(password)
        print(password)
        user.save()
        return user

    @staticmethod
    def get_all_users():
        return User.objects.all()

    @staticmethod
    def get_profile_by_user(user):
        return Profile.objects.get(user=user)
