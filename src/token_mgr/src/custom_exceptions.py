
class CustomHTTPException(Exception):
    """
    Generic exception class for all HTTP exceptions.
    """
    pass


class BadRequestException(CustomHTTPException):
    """
    Should be raised when a request is not formatted correctly.
    The server should respond with 400.
    """
    pass


class NotFoundException(CustomHTTPException):
    """
    Should be raised when an item is not found.
    The server should respond with 404.
    """
    pass


class UnauthorizedException(CustomHTTPException):
    """
    Should be raised when the user is not allowed to access something.
    The server should respond with 401.
    """
    pass
