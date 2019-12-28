"""Django middleware helper to set the CURRENT_ORG as a thread local variable.

We have a multi tenant app in which user can belong to multiple organizations.
The user is provided a context menu to switch between orgs and once a user
chooses an Org, we need restrict all the information shown to that org.

When a user logs in to the website we need to show information pertaining
to a default org and when a user switches to a different org we should save
this org and use it in all other views.

Currently the default Org is the first one in the list. It will be saved in
a variable called CURRENT_ORG and will only be set if not already set.
"""

import threading

_thread_locals = threading.local()


def get_current_org():
    """Return the current Org object corresponding to the Org chosen by User.
    :rtype: class Organization.models.Org
    :returns: Org object
    """
    return getattr(_thread_locals, 'CURRENT_ORG', None)


try:
    # Django >= 1.10
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    # Not required for Django <= 1.9, see:
    # https://docs.djangoproject.com/en/1.10/topics/http/middleware/#upgrading-pre-django-1-10-style-middleware
    MiddlewareMixin = object


class CurrentOrgMiddleware(MiddlewareMixin):
    """Saves the a default Org as Current Org in thread local"""

    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_request(self, request):
        """Called on each request, before Django decides which view to execute.
        :type request: :class:`~django.http.request.HttpRequest`
        :param request: Django http request.
        """
        if hasattr(_thread_locals, 'CURRENT_ORG') is False:
            # Only set this variable if not already set. This also prevents
            # resetting the variable on every request.
            _thread_locals.CURRENT_ORG = request.user.org

        # TODO: Currently user can join one org. Once user.org becomes a
        # manytomany list set to the first one in the list.
