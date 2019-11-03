"""Django middleware helper to capture a request.
The request is stored on a thread-local so that it can be
inspected by other helpers.
"""

import threading

_thread_locals = threading.local()


def _get_django_request():
    """Get Django request from thread local.
    :rtype: str
    :returns: Django request.
    """
    return getattr(_thread_locals, 'request', None)


try:
    # Django >= 1.10
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    # Not required for Django <= 1.9, see:
    # https://docs.djangoproject.com/en/1.10/topics/http/middleware/#upgrading-pre-django-1-10-style-middleware
    MiddlewareMixin = object


class RequestMiddleware(MiddlewareMixin):
    """Saves the request in thread local"""

    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_request(self, request):
        """Called on each request, before Django decides which view to execute.
        :type request: :class:`~django.http.request.HttpRequest`
        :param request: Django http request.
        """
        _thread_locals.request = request