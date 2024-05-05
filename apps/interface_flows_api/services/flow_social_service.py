from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist

from apps.interface_flows_api.models import Comment, Flow, Like, User


class FlowSocialService:
    @staticmethod
    def comment_flow(flow: Flow, user: User, text: str) -> Comment:
        return Comment.objects.create(flow=flow, author=user.profile, text=text)

    @staticmethod
    def like_flow(flow: Flow, user: User, like: bool = True) -> Flow:
        if like:
            Like.objects.get_or_create(flow=flow, user=user.profile)
        else:
            try:
                like = Like.objects.get(flow=flow, user=user.profile)
                like.delete()
            except ObjectDoesNotExist:
                raise ObjectDoesNotExist

        return flow


flow_social_service = FlowSocialService()
