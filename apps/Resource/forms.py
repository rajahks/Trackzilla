from django import forms
from .models import Resource
from apps.Organization.models import Org
from django.contrib.auth import get_user_model

# Get the current custom User Model.
User = get_user_model()


class ResourceDetailForm(forms.ModelForm):
    """ModelForm which handles the detail page of a resource. It is like a regular
    form but makes all the fields disabled so that the user cannot change any values.
    Also we need to restrict values like 'current_user' and 'device_admin' to
    contain only users from the current org
    """

    def __init__(self, *args, org, **kwargs):
        """Constructor which accepts Org and carries out the following tasks:
        1) Disable all the fields so that user cannot edit and field.
        2) Restrict the queryset of user fields to contain elements only in the org.

        Arguments:
            org {apps.Organization.models.Org} -- Org object to which this resource belongs.
        """

        super(ResourceDetailForm, self).__init__(*args, **kwargs)
        self.fields['current_user'].queryset = org.user_set.all()
        self.fields['device_admin'].queryset = org.user_set.all()
        for field in self.fields.values():
            field.disabled = True

    class Meta:
        model = Resource
        exclude = ['history', 'previous_user', 'org']


class ResourceCreateForm(forms.ModelForm):
    """ModelForm to create a Resource. It removes few fields which the user wouldn't need
    and also restricts the entries that will be shown to select the 'current_user' and
    'device_admin'. They will be restricted to only have users pertaining to the current
    org of the logged in user.
    """
    def __init__(self, *args, in_org, **kwargs):
        """Accepts the keyword arg 'in_org' to restrict entries only to that org.

        Arguments:
            in_org {apps.Organization.models.Org} -- Org in which we want the resource
            to be created.
        """
        super(ResourceCreateForm, self).__init__(*args, **kwargs)
        self.fields['current_user'].queryset = in_org.user_set.all()
        self.fields['device_admin'].queryset = in_org.user_set.all()

    class Meta:
        model = Resource
        exclude = ['org', 'history', 'previous_user', 'status']
        # Org has to be set by the view to the user's current Org.
        # status will also be set to RES_ASSIGNED in the view.

class ResourceUpdateForm(forms.ModelForm):
    """ModelForm to Update a Resource. It removes few fields which the user wouldn't need
    and also restricts the entries that will be shown to select the 'current_user' and
    'device_admin'. They will be restricted to only have users pertaining to the current
    org of the logged in user.
    """
    def __init__(self, *args, in_org, **kwargs):
        """Accepts the keyword arg 'in_org' to restrict entries only to that org.

        Arguments:
            in_org {apps.Organization.models.Org} -- Org to which the resource belongs.
        """
        super(ResourceUpdateForm, self).__init__(*args, **kwargs)
        self.fields['current_user'].queryset = in_org.user_set.all()
        self.fields['device_admin'].queryset = in_org.user_set.all()

    class Meta:
        model = Resource
        exclude = ['org', 'history', 'previous_user', 'status']
        # Org has to be set by the view to the user's current Org.
        # status will also be set to RES_ASSIGNED in the view.
