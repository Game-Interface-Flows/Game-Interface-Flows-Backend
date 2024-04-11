from rest_framework.exceptions import APIException


class UnverifiedFlowExistsException(Exception):
    """Exception is raised when user tries to create a new flow even they have a unverified one."""

    pass


class MLServicesUnavailableException(Exception):
    """Exception is raised when the ML service is unreachable."""

    pass


class PrivateFlowException(Exception):
    """Exception is raised when authorized user tries to get access to a private flow."""

    pass


class UnverifiedFlowExists(APIException):
    """Exception for flows limit."""

    status_code = 403
    default_detail = (
        "You have reached the maximum limit of flows on verification. Please wait until your "
        "previous flows will be verified."
    )
    default_code = "flows_limit"


class MLServiceUnavailable(APIException):
    """Exception for ML service."""

    status_code = 503
    default_detail = "ML Service temporarily unavailable, try again later."
    default_code = "service_unavailable"
