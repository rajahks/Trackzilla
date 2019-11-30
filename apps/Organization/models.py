from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

#Get the current custom User Model.
User = get_user_model()


class Org(models.Model):
    # Name of the organization. A user can create multiple orgs.
    org_name = models.CharField(max_length=50)

    # Admin for the Org. Generally the person who creates the org.
    # Do not allow the user to be deleted if he is an admin of any Org
    admin_id = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="adminForOrg")

    def __str__(self):
        return self.org_name

    def get_absolute_url(self):
        return reverse("org-detail", kwargs={"pk": self.pk})


class Team(models.Model):
    team_name = models.CharField(max_length=50)

    # Admins for the team. Yes, a team can have multiple admins. However only a member of this
    # team must be allowed be added to this list.
    team_admins = models.ManyToManyField(User, related_name='team_admin_for', blank=True)

    # Org to which the team belongs. Do not allow the parent Org to be deleted if there are teams in it.
    org = models.ForeignKey(Org, on_delete=models.PROTECT)

    # Teams are recursive. One team can contain multiple teams within itself.
    sub_teams = models.ManyToManyField('self', related_name='sub_team_list', blank=True)

    # Members of the team.
    team_members = models.ManyToManyField(User, related_name='team_member_of', blank=True)

    def __str__(self):
        return self.team_name

    def get_absolute_url(self):
        return reverse("team-detail", kwargs={"pk": self.pk})
