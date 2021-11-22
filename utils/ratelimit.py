from rest_framework.views import exception_handler as drf_exception_handler
from ratelimit.exceptions import Ratelimited


def exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = drf_exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if isinstance(exc, Ratelimited):
        response.data['detail'] = 'Too many requests, try again later.'
        response.status_code = 429

    return response
