from rest_framework.response import Response
from rest_framework import status
from functools import wraps


def required_parames(request_attr='query_params', params=None):
    # Usually parameters should not use a mutable value
    # In this simple case, we use params = []
    if params is None:
        params = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(instance, request, *args, **kwargs):
            data = getattr(request, request_attr)
