from django.contrib.auth.mixins import UserPassesTestMixin
from apps.Resource.models import Resource
# Logging
import logging

logger = logging.getLogger(__name__)


class UserHasAccessToResourceMixin(UserPassesTestMixin):

    # Override the function from UserPassesTestMixin to determine if user has access to the object.
    def test_func(self):
        obj = self.get_object()
        if isinstance(obj, Resource):
            if obj.org == self.request.user.org:
                # Resource Object part of logged in user's current org.
                # In future if a user can be part of multiple Orgs then change this
                # condition to "obj.org in self.request.user.orgs.all()"
                logger.debug("User %s given access to %s as both are part of Org %s" % (self.request.user.get_email(),
                    obj.name, obj.org))
                return True
            else:
                logger.warning("User %s (%s) DENIED access to %s (%s) as both are not part of same Org" %
                    (self.request.user.get_email(), self.request.user.org, obj.name, obj.org))
                return False
        else:
            logger.error("Object not of type resource. Type:%s" % (type(obj),))
            return False
