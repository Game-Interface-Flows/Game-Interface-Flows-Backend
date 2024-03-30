class MLServicesUnavailableException(Exception):
    """Exception raised when the ML service is unreachable."""

    pass


class PrivateFlowException(Exception):
    """Exception raised when authorized user tries to get access to a private flow."""

    pass
