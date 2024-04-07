from rest_framework.exceptions import APIException


class MLServicesUnavailableException(Exception):
    """Exception raised when the ML service is unreachable."""

    pass


class PrivateFlowException(Exception):
    """Exception raised when authorized user tries to get access to a private flow."""

    pass


class MLServiceUnavailable(APIException):
    """Exception for ML service."""

    status_code = 503
    default_detail = "ML Service temporarily unavailable, try again later."
    default_code = "service_unavailable"
