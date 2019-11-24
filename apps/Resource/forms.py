from django import forms
from .models import Resource
from apps.Organization.models import Org
from django.contrib.auth import get_user_model

#Get the current custom User Model.
User = get_user_model()

class ResourceDetailForm(forms.ModelForm):
    name = forms.CharField(disabled=True)
    serial_num = forms.CharField(disabled=True)
    current_user = forms.ModelChoiceField(queryset=User.objects.all(), disabled=True) #TODO: All the three queries should be org specific.
    device_admin = forms.ModelChoiceField(queryset=User.objects.all(), disabled=True)
    # status = forms.ChoiceField(disabled=True)  # TODO: Commented out because this was causing the detail view to have an empty status field.
    org = forms.ModelChoiceField(queryset=Org.objects.all(), disabled=True)
    # TODO : Figure out to make description text area also non editable

    class Meta:
        model = Resource
        fields = ['name', 'serial_num', 'current_user', 'device_admin', 'status', 'description', 'org']
