from django import forms
# from .models import AssetUser
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from apps.Organization.models import Org

#Get the current custom User Model.
User = get_user_model()

class UserRegisterForm(UserCreationForm):
    # email field is not provided in UserCreationForm by default. Add it.
    email = forms.EmailField()

    # The model I want this form to interact with. And the fields that I want to be shown in this form.
    # When a form.save() is called for this custom form, this is the model that's going to be updated.
    # TODO : check if we would need firstname ,lastname fields here.
    class Meta:
        model = User
        fields = [ 'email', 'name', 'password1', 'password2']


class UserDetailForm(forms.ModelForm):
    email = forms.CharField(disabled=True)
    name = forms.CharField(disabled=True)
    org = forms.ModelChoiceField(queryset=Org.objects.all(), disabled=True)  #TODO: This should only show the orgs he is part of not all.

    class Meta:
        model = User
        fields = ['email', 'name', 'org']
