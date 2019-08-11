from django.db import models
from apps.Users.models import User


class Team(models.Model):
    team_name = models.CharField(max_length=30)
    admin_id = models.ForeignKey(User, on_delete=models.CASCADE)
    sub_teams = models.ManyToManyField('self' ,related_name='sub_team_list', blank=True, null=True)
    team_members = models.ManyToManyField(User ,related_name='team_member_list', blank=True, null=True)

    def __str__(self):
        return self.team_name


class Org(models.Model):
    org_name = models.CharField(max_length=30)
    admin_id = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.org_name