from django import forms
from .models import AssetUser
from django.contrib.auth.forms import UserCreationForm


class UserRegisterForm(UserCreationForm):
    # email field is not provided in UserCreationForm by default. Add it.
    email = forms.EmailField()

    # The model I want this form to interact with. And the fields that I want to be shown in this form.
    # When a form.save() is called for this custom form, this is the model that's going to be updated.
    class Meta:
        model = AssetUser
        fields = ['username', 'email', 'password1', 'password2']