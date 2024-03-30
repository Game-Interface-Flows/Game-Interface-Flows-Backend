from rest_framework import status
from rest_framework.response import Response


class NotFoundResponse(Response):
    def __init__(self, object_name, object_id):
        super().__init__(
            {
                "error": f"Failed to get {object_name}",
                "message": f"{object_name} with id={object_id} not found.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )


class NonAuthoritativeResponse(Response):
    def __init__(self, object_name):
        super().__init__(
            {
                "error": f"Failed to get {object_name}.",
                "message": f"You do not have rights to access this {object_name}.",
            },
            status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION,
        )
