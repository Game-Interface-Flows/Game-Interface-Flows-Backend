from rest_framework.exceptions import APIException


class UnverifiedFlowExistsException(Exception):
    """Exception is raised when user tries to create a new flow even they have a unverified one."""

    pass


class MLServicesUnavailableException(Exception):
    """Exception is raised when the ML service is unreachable."""

    pass


class MLServicesException(Exception):
    """Exception is raised when the ML service does not return OK status."""

    pass


class PrivateFlowException(Exception):
    """Exception is raised when authorized user tries to get access to a private flow."""

    pass


class VideoProcessingException(Exception):
    """ "Exception is raised when problem with video processing happens."""

    pass


class UnverifiedFlowExists(APIException):
    """Response for flows limit exception."""

    status_code = 403
    default_detail = (
        "You have reached the maximum limit of flows on verification. Please wait until your "
        "previous flows will be verified."
    )
    default_code = "flows_limit"


class MLServiceUnavailable(APIException):
    """Response for ML service exception."""

    status_code = 503
    default_detail = "ML Service temporarily unavailable, try again later."
    default_code = "service_unavailable"


class VideoProcessing(APIException):
    """Response for video processing exception."""

    status_code = 500
    default_detail = "..."
    default_code = "server_problem"
