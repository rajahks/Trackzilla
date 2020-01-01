from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

#Get the current custom User Model.
User = get_user_model()

import logging
logger = logging.getLogger(__name__)

class Org(models.Model):
    # Name of the organization. A user can create multiple orgs.
    org_name = models.CharField(max_length=50)

    # Admin for the Org. Generally the person who creates the org.
    # Do not allow the user to be deleted if he is an admin of any Org
    admin = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="adminForOrg")

    # As the join link could be leaked outside an org, we do not want people outside an
    # org to join the Org. So we allow the admin to specify the domain names to allow.
    # When specified, only users having email ids with that domain will be allowed to join.
    # Since outside users cannot obtain email ids with that domain, it will thus restrict
    # illegal access.For this to be effective we need to validate user email with a
    # verification email.
    # Eg: If '@abc.com' is specified then only users having email ids with '@abc.com' will
    # be allowed to join.
    # TODO: In future make this a comma separated list so that a admin can specify a list
    # of allowed domain. We can have another field where user specifies a list of email
    # ids which are allowed to join.
    allowed_email_domain = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.org_name

    def get_absolute_url(self):
        return reverse("Org:org-detail", kwargs={"pk": self.pk})

    def get_join_link(self):
        """Returns the link which can be used to join the organization.
        """
        return reverse('Org:org-join', kwargs={'pk':self.pk, 'OrgName':self.org_name})

    def is_email_allowed(self, email_id):
        """Used to check if the emailId passed can join the org. This is decided based on
        whether 'Allowed email domain' is configured. In future when the allow list 
        criteria changes the logic in this function will need to be amended.

        Arguments:
            email_id {str} -- email id of the user wanting to join the group

        Returns:
            True - If user is allowed to join the group
            False - If user is not allowed.
        """
        if len(self.allowed_email_domain) == 0:
            # no rules configured. Allow everyone to join.
            return True

        # Extract the domain portion including @ of the user's email id.
        sepPos = email_id.rfind('@')
        if sepPos == -1:
            # could not find the '@' symbol. Invalid email id.
            logger.error("Email id:%s trying to join Org:%s"%(email_id, self.org_name))
            return False

        emailDomain = email_id[sepPos:]
        if emailDomain.lower().strip() == self.allowed_email_domain.lower().strip():
            logger.info("User %s allowed to join Org %s"%(email_id, self.org_name))
            return True
        else:
            logger.info("User %s Not allowed to join Org %s. Only email id ending with %s allowed"%
                (email_id, self.org_name, self.allowed_email_domain))
            return False

    def get_name(self):
        return self.org_name


class Team(models.Model):
    team_name = models.CharField(max_length=50)

    team_description = models.CharField(max_length=200, blank=True)

    # Admins for the team. Yes, a team can have multiple admins. However only a member of this
    # team must be allowed be added to this list. Every team must have atleast one admin
    # TODO: Make sure during create, the user who is creating is made the admin of the team
    # automatically
    team_admins = models.ManyToManyField(User, related_name='team_admin_for')

    # Org to which the team belongs. Do not allow the parent Org to be deleted if there are teams in it.
    org = models.ForeignKey(Org, on_delete=models.PROTECT, related_name='team_set')

    # Teams are recursive. One team can contain multiple teams within itself.
    # NOTE: Commented sub_teams and adding parent_team
    # sub_teams = models.ManyToManyField('self', related_name='sub_team_list', blank=True)

    # Having recursive teams can lead to cyclic issues(i.e parent team
    # addded as a sub team. To avoid this we need to filter out all parent and ancestors
    # when showing the list to add subteams).

    # Also it would be better to have a single ForeignKey to the parent team.
    # This way when creating the sub-team we can choose who the parent is vs going and
    # adding a subteam in the parent team. Its much easier and another team admin will not
    # need to get involved. However this still can lead to cyclic issues as follows:
    # Lets say we have 3 teams Team Base, Team Parent and Team Child. We can edit such
    # that Team Parent's parent is Team Child and Team Child's parent is Team Parent.
    # And so the cyclic issue.
    # To solve this, in the view we need to filter out all children when showing the
    # list of parents.
    parent_team = models.ForeignKey('self', on_delete=models.PROTECT,
        related_name='sub_team_list', blank=True, null=True)

    # Members of the team.
    team_members = models.ManyToManyField(User, related_name='team_member_of', blank=True)

    def __str__(self):
        return self.team_name

    def get_absolute_url(self):
        return reverse("Org:team-detail", kwargs={"pk": self.pk})

    def get_name(self):
        return self.team_name

    def get_team_hierarchy(self):
        """Returns a string representation of the hierarchy to the Org.
        This would allow us to easily visualize the parents and also the Org.

        Eg: If a team 'Team1' is part of org Trackzilla then the path is
        'Trackzilla / Team1'. If Team1 has a sub-team 'Team2' then path of Team2 is
        'Trackzilla / Team1 / Team2'

        Enhancement: This currently returns a string representation. It would be good
        to have each of the parent and the org as clickable links so that we can easily
        navigate.

        Returns:
            str -- String representation of the path to the org.
        """
        team = self
        path = team.get_name()
        while team.parent_team is not None:
            path = team.parent_team.get_name() + " / " + path
            team = team.parent_team

        # append the Org
        path = "%s / %s" % (self.org.get_name(), path)
        return path
