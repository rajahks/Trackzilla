from django import forms
from .models import Org, Team
from apps.Users.models import AssetUser


class OrgDetailForm(forms.ModelForm):
    org_name = forms.CharField(disabled=True)
    admin_id = forms.ModelChoiceField(queryset=AssetUser.objects.all(), disabled=True)

    class Meta:
        model = Org
        fields = ['org_name', 'admin_id']


class TeamDetailForm(forms.ModelForm):
    team_name = forms.CharField(disabled=True)
    org_id = forms.ModelChoiceField(queryset=Org.objects.all(),  disabled=True)
    team_admins = forms.ModelMultipleChoiceField(queryset=AssetUser.objects.all(), disabled=True)
    sub_teams = forms.ModelMultipleChoiceField(queryset=Team.objects.all(), disabled=True)
    team_members = forms.ModelMultipleChoiceField(queryset=AssetUser.objects.all(), disabled=True)

    class Meta:
        model = Team
        fields = ['team_name', 'team_admins', 'org_id', 'sub_teams', 'team_members']