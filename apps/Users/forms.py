from django import forms
from .models import AssetUser
from django.contrib.auth.forms import UserCreationForm
from apps.Organization.models import Org


class UserRegisterForm(UserCreationForm):
    # email field is not provided in UserCreationForm by default. Add it.
    email = forms.EmailField()

    # The model I want this form to interact with. And the fields that I want to be shown in this form.
    # When a form.save() is called for this custom form, this is the model that's going to be updated.
    # TODO : check if we would need firstname ,lastname fields here.
    class Meta:
        model = AssetUser
        fields = ['username', 'email', 'password1', 'password2']


class UserDetailForm(forms.ModelForm):
    username = forms.CharField(disabled=True)
    email = forms.CharField(disabled=True)
    org_id = forms.ModelChoiceField(queryset=Org.objects.all(), disabled=True)

    class Meta:
        model = AssetUser
        fields = ['username', 'email', 'org_id']