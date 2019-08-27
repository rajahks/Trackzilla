from django.db import models
from apps.Users.models import AssetUser


class Org(models.Model):
    # Name of the organization. A user can create multiple orgs.
    org_name = models.CharField(max_length=50)

    # Admin for the Org. Generally the person who creates the org. If the admin user entry is deleted,
    # we set this admin field here to NULL.
    admin_id = models.ForeignKey(AssetUser, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.org_name


class Team(models.Model):
    team_name = models.CharField(max_length=50)

    # Admins for the team. Yes, a team can have multiple admins. However only a member of this
    # team must be allowed be added to this list.
    team_admins = models.ManyToManyField(AssetUser, related_name='team_admins_list', blank=True)

    # Org to which the team belongs. Do not allow the parent Org to be deleted if there are teams in it.
    org_id = models.ForeignKey(Org, on_delete=models.PROTECT)

    # Teams are recursive. One team can contain multiple teams within itself.
    sub_teams = models.ManyToManyField('self', related_name='sub_team_list', blank=True)

    # Members of the team.
    team_members = models.ManyToManyField(AssetUser, related_name='team_member_list', blank=True)

    def __str__(self):
        return self.team_name


