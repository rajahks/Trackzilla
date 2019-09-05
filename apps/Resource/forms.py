from django import forms
from .models import Resource
from apps.Organization.models import Org
from apps.Users.models import AssetUser


class ResourceDetailForm(forms.ModelForm):
    name = forms.CharField(disabled=True)
    serial_num = forms.CharField(disabled=True)
    current_user = forms.ModelChoiceField(queryset=AssetUser.objects.all(), disabled=True)
    device_admin = forms.ModelChoiceField(queryset=AssetUser.objects.all(), disabled=True)
    status = forms.ChoiceField(disabled=True)
    org_id = forms.ModelChoiceField(queryset=Org.objects.all(), disabled=True)
    # TODO : Figure out to make description text area also non editable

    class Meta:
        model = Resource
        fields = ['name', 'serial_num', 'current_user', 'device_admin', 'status', 'description', 'org_id']