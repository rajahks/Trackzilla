from django import forms
from .models import Org, Team
from django.contrib.auth import get_user_model

#Get the current custom User Model.
User = get_user_model()

class OrgDetailForm(forms.ModelForm):
    org_name = forms.CharField(disabled=True)
    admin_id = forms.ModelChoiceField(queryset=User.objects.all(), disabled=True) # TODO: This should be Org specific.
    allowed_email_domain = forms.CharField(disabled=True)

    class Meta:
        model = Org
        fields = ['org_name', 'admin_id', 'allowed_email_domain']



class TeamDetailForm(forms.ModelForm):
    team_name = forms.CharField(disabled=True)
    orgs = forms.ModelChoiceField(queryset=Org.objects.all(),  disabled=True)  #TODO: A team should ideally belong to a single org.
    team_admins = forms.ModelMultipleChoiceField(queryset=User.objects.all(), disabled=True)  #TODO: All 3 below calls Should be Org specific.
    sub_teams = forms.ModelMultipleChoiceField(queryset=Team.objects.all(), disabled=True)
    team_members = forms.ModelMultipleChoiceField(queryset=User.objects.all(), disabled=True)

    class Meta:
        model = Team
        fields = ['team_name', 'team_admins', 'orgs', 'sub_teams', 'team_members']
