from django.contrib.auth.mixins import UserPassesTestMixin
from apps.Resource.models import Resource
from apps.Organization.models import Team, Org
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
# Logging
import logging

logger = logging.getLogger(__name__)


class UserHasAccessToResourceMixin(UserPassesTestMixin):

    # Override the function from UserPassesTestMixin to determine if user has access to the object.
    def test_func(self):

        # In order to check if the user has access to a resource, we need to first fetch
        # the resource. In order to fetch the resource we will use the 'pk' field which is
        # part of all resource urls.
        # Note: It is very important that we need to have the 'pk' as without it we will
        # not be able to fetch the object.

        if 'pk' not in self.kwargs.keys():
            logger.error("pk not present. Cannot fetch resource. Denying access by returning False")
            return False

        # Fetch the object.
        obj = get_object_or_404(Resource, pk=self.kwargs['pk'])
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


class UserHasAccessToTeamMixin(UserPassesTestMixin):

    # Override the function from UserPassesTestMixin to determine if user has access to the object.
    def test_func(self):
        # Fetch the object.
        obj = self.get_object()
        if isinstance(obj, Team):
            if obj.org == self.request.user.org:
                # Team Object part of logged in user's current org.
                # In future if a user can be part of multiple Orgs then change this
                # condition to "obj.org in self.request.user.orgs.all()"
                logger.debug("User %s given access to team %s as both are part of Org %s" %
                    (self.request.user.get_email(), obj.get_name(), obj.org.get_name()))
                return True
            else:
                logger.warning("User %s (%s) DENIED access to team %s (%s) as both are not part of same Org" %
                    (self.request.user.get_email(), self.request.user.org,
                     obj.get_name(), obj.org.get_name()))
                return False
        else:
            logger.error("Object not of type Team. Type:%s" % (type(obj),))
            return False


class UserCanModifyTeamMixin(UserHasAccessToTeamMixin):

    # Override the function from UserHasAccessToTeamMixin to determine if user has access 
    # to update the team.
    def test_func(self):
        # call the base class function and check if the user has access to team
        hasAccessResult = super(UserCanModifyTeamMixin, self).test_func()
        if hasAccessResult is False:
            return False

        # Now check of the user is an admin. Only an admin of the team can update the team
        obj = self.get_object()
        if isinstance(obj, Team):
            if self.request.user in obj.team_admins.all():
                # User is an admin. Allow to modify
                logger.debug("User %s given access to UPDATE team %s as user is an admin of the team." %
                    (self.request.user.get_email(), obj.get_name()))
                return True
            else:
                logger.warning("User %s (%s) DENIED access to UPDATE team %s (%s) as not an admin" %
                    (self.request.user.get_email(), self.request.user.org,
                     obj.get_name(), obj.org.get_name()))
                return False
        else:
            logger.error("Object not of type Team. Type:%s" % (type(obj),))
            return False


class UserHasAccessToOrgMixin(UserPassesTestMixin):

    # Override the function from UserPassesTestMixin to determine if user has
    # access to the Org.
    def test_func(self):
        # In order to check if the user has access to a Org, we need to first fetch
        # the Org. In order to fetch the Org we will use the 'pk' field which is
        # part of all Org urls.
        # Note: It is very important that we need to have the 'pk' as without it we will
        # not be able to fetch the object.

        if 'pk' not in self.kwargs.keys():
            logger.error("pk not present. Cannot fetch Org. Denying access by returning False")
            return False

        # Fetch the object.
        obj = get_object_or_404(Org, pk=self.kwargs['pk'])
        if isinstance(obj, Org):
            if obj == self.request.user.org:
                # Logged in user's belongs to the same Org. Allow access
                # In future if a user can be part of multiple Orgs then change this
                # condition to "obj.org in self.request.user.orgs.all()"
                logger.debug("User %s given access to '%s' Org as both are part of same Org" %
                    (self.request.user.get_email(), obj.get_name()))
                return True
            else:
                logger.warning("User %s (%s) DENIED access to %s Org as both are not part of same Org" %
                    (self.request.user.get_email(), self.request.user.org, obj.get_name()))
                return False
        else:
            logger.error("Object not of type Org. Type:%s" % (type(obj),))
            return False


class UserCanDeleteOrgMixin(UserPassesTestMixin):
    # Override the function from UserPassesTestMixin to determine if user has
    # access to the Org.
    def test_func(self):
        # In order to check if the user can delete an Org, we need to first fetch
        # the Org. In order to fetch the Org we will use the 'pk' field which is
        # part of all Org urls.
        # Note: It is very important that we need to have the 'pk' as without it we will
        # not be able to fetch the object.

        if 'pk' not in self.kwargs.keys():
            logger.error("pk not present. Cannot fetch Org. Denying access by returning False")
            return False

        # Fetch the object.
        obj = get_object_or_404(Org, pk=self.kwargs['pk'])
        if isinstance(obj, Org):
            if obj.admin == self.request.user:
                # Logged in user's is the Admin of the Org. Allow access
                # In future if we can have Multiple Admins then change this
                # condition to "self.request.user in obj.admin.all()"
                logger.debug("User %s given access to delete '%s' Org as user is an admin." %
                    (self.request.user.get_email(), obj.get_name()))
                return True
            else:
                logger.warning("User %s (%s) DENIED access to delete '%s' Org as NOT an admin of Org" %
                    (self.request.user.get_email(), self.request.user.org, obj.get_name()))
                return False
        else:
            logger.error("Object not of type Org. Type:%s" % (type(obj),))
            return False


class UserHasAccessToViewUserMixin(UserPassesTestMixin):

    # Override the function from UserPassesTestMixin to determine if user has
    # access to the object.
    def test_func(self):
        # Fetch the object.
        obj = self.get_object()
        user_model = get_user_model()  # Should return AssetUser model

        if isinstance(obj, user_model):
            if obj.org == self.request.user.org:
                # User Object part of logged in user's current org.
                # In future if a user can be part of multiple Orgs then change this
                # condition to "obj.org in self.request.user.orgs.all()"
                logger.debug("User %s given access to view user %s as both are part of Org %s" %
                    (self.request.user.get_email(), obj.get_email(), obj.org.get_name()))
                return True
            else:
                logger.warning("User %s (%s) DENIED access to view user %s (%s) as both are not part of same Org" %
                    (self.request.user.get_email(), self.request.user.org,
                     obj.get_email(), obj.org.get_name()))
                return False
        else:
            logger.error("Object not of type AssetUser. Type:%s" % (type(obj),))
            return False


class UserCanDelUserMixin(UserPassesTestMixin):
    # Override the function from UserPassesTestMixin to determine if user has
    # access to delete the user object.
    def test_func(self):
        # Fetch the User object by using the pk from the url.
        # Note: It is very important that we need to have the 'pk' as without it we will
        # not be able to fetch the object.

        if 'pk' not in self.kwargs.keys():
            logger.error("pk not present. Cannot fetch User object. Denying access by returning False")
            return False

        # Fetch the object.
        user_model = get_user_model()  # Should be AssetUser
        obj = get_object_or_404(user_model, pk=self.kwargs['pk'])
        if isinstance(obj, user_model):
            # TODO: check if user's Org is not None.
            # first check if the logged in user and the user obj belong to the same Org
            if obj.org != self.request.user.org:
                logger.warning("User %s (%s) DENIED access to view user %s (%s) as both are not part of same Org" %
                    (self.request.user.get_email(), self.request.user.org,
                     obj.get_email(), obj.org.get_name()))
                return False

            # Now check if the logged in user is the admin of the Org as only org admin
            # can delete a user.
            if obj.org.admin != self.request.user:
                # Logged in user is NOT the Admin of the Org that the user is part of.
                # In future if we can have Multiple Admins then change this
                # condition to "self.request.user not in obj.org.admin.all()"
                logger.warning("User %s (%s) DENIED access to delete '%s' user as NOT an admin of Org" %
                    (self.request.user.get_email(), self.request.user.org.get_name(),
                     obj.get_email()))
                return False

            # User passed all tests. Allow access.
            logger.debug("User '%s' given access to delete '%s' user as user is an admin." %
                (self.request.user.get_email(), obj.get_email()))
            return True
        else:
            logger.error("Object not of type AssetUser. Type:%s" % (type(obj),))
            return False