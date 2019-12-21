from django.db import models
from apps.Organization.models import Org
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.ChangeHistory.middleware import _get_django_request
from apps.ChangeHistory.models import ChangeHistoryMixin

import logging
logger = logging.getLogger(__name__)

#Get the current custom User Model.
User = get_user_model()

def CustomProcessDictHook(instance, object_dict, *args, **kwargs):
    """Hook function which will be set to the field 'history__process_dict_hook'
    User FK in Resource get serialized to a number. This replaces the userID number with 
    a username.

    Arguments:
        instance {Resource} -- Resource object is passed as self
        object_dict {dict} -- Dictionary returned by model_to_dict.
    """
    for field in object_dict:
            # for AssetUser
            if hasattr(instance,field):
                field_val = getattr(instance,field)
                
                if field_val is not None and issubclass(field_val.__class__, User):
                    object_dict[field] = field_val.get_username()

            # TODO: add other non-serializable field types or fields which need custom
            # processing.
    return

def get_loggedin_user(*args,**kwargs):
    """Custom function called by the ChangeHistory mixin to store the who changed the field.
    This function returns the value to be stored in the 'who' field.

    In our app we want this to be our logged in user. The logged in user is
    present in the request object which is stored as a thread local variable using
    the RequestMiddleware. Fetch the request object by calling _get_django_request() and
    return the user value.

    Returns:
        str -- The value to be stored in the who field.
    """
    who = ''
    request_obj = _get_django_request()
    if request_obj is not None:
        # We wish to store the email id in the who field.
        # TODO: Check if we want email or username.
        who = request_obj.user.email

    return who

class Resource( ChangeHistoryMixin, models.Model):
    # Name of the resource.
    name = models.CharField(max_length=50)
    # serial num used to uniquely identify the resource. Generally AlphaNumeric. 
    serial_num = models.CharField(max_length=50)

    # FK to the User who is currently using the device.
    # We should not allow the User object to be deleted when he has resources in his name.
    # The resources should be moved out and only then the resource should be deleted.
    # We achieve this constraint by using the models.PROTECT constraint.
    # https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.PROTECT
    current_user = models.ForeignKey(User, on_delete=models.PROTECT,
                                     related_name='res_being_used')

    # FK to the previous user of the device. The field is updated when the resource is
    # transferred from one person to another person. Current_user will be the one who to
    # whom the resource is assigned and the previous_user will be the one who previously
    # was using the resource.
    previous_user = models.ForeignKey( User, on_delete=models.SET_NULL, blank=True,
                                       null=True, related_name='res_prev_used')

    # FK to the User who is currently managing the device.
    # This user would have admin privileges over the device.
    # TODO: Yet to be decided what these admin privileges are (This would mostly allow the user to edit fields)
    # Like the 'current user' above we do not allow the Device Admin User object
    # to be deleted when he has Resources assigned to him.
    # Enforce the constraint.
    device_admin = models.ForeignKey(User, on_delete=models.PROTECT,
                                     related_name='res_being_managed')

    # The related_name allows us to fetch the resource list from the User model itself. Very useful as we would mostly
    # need to fetch these details per user. Might be better to let the ORM take care of this for us.

    # A resource could have the following states:
    # 'Unassigned' - When the resource is not assigned to any User
    # 'Assigned' - When the resource is assigned to a User and the user has not get Ackd it
    # 'Acknowledged' - When the assigned user acks that the resource is available with him.
    # 'Disputed' - Set to Resources which the current user denies owning them.
    # Resources which are 'Unassigned' and which are 'Assigned' but not 'Acknowledged'
    # i.e. disputed have to be notified to the device admin.

    RES_UNASSIGNED = 'R_UASS'
    RES_ASSIGNED = 'R_ASS'
    RES_ACKNOWLEDGED = 'R_ACK'
    RES_DISPUTE = 'R_DISP'

    RES_STATUS_CHOICES = [
        (RES_UNASSIGNED, 'Unassigned'),
        (RES_ASSIGNED, 'Assigned'),
        (RES_ACKNOWLEDGED, 'Acknowledged'),
        (RES_DISPUTE, 'Disputed')
    ]

    # TODO: Check if the states defined above are ok - should we have a conflicted/disputed status?
    status = models.CharField(choices=RES_STATUS_CHOICES, default=RES_UNASSIGNED, max_length=20)

    # Any additional information about the device to go into this field.
    description = models.TextField()

    # TODO: Add a FK to a organisation.
    # Every resource will belong to an Organisation. This way we can have
    # resources belonging to different orgs on the same DB and filter them
    # based on a logged in user's organization.
    org = models.ForeignKey(Org, on_delete=models.PROTECT, null=True, related_name='resource_set')


    # Configure the Hook functions used by ChangeHistoryMixin.
    history__process_dict_hook = CustomProcessDictHook
    history__get_user_hook = get_loggedin_user
    history__max_entry_count = 100  #TODO: Make this configurable via global settings

    class Meta:
        verbose_name = "resource"
        verbose_name_plural = "resources"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Resource:resource-detail", kwargs={"pk": self.pk})

    def get_update_url(self):
        return reverse("Resource:resource-update", kwargs={"pk": self.pk})

    def get_acknowledge_url(self):
        """Called from a view to fetch the url which can be used to ack owning the device. 
        The pk of the device is embedded into the link.

        Returns:
            str -- Url of the form  'resource/<int:pk>/acknowledge'

        Note: The value returned by this should be appended to server uri returned by
        build_absolute_url. The call in a view would be something like
        'request.build_absolute_uri(resource.get_acknowledge_url())'
        """
        return  "/resource/%d/acknowledge"%(self.pk,)

    def get_deny_url(self):
        """Called from a view to fetch the url which can be used to deny owning the device.
        The pk of the device is embedded into the link.

        Returns:
            str -- Url of the form 'resource/<int:pk>/deny'

        Note: The value returned by this should be appended to server uri returned by
        build_absolute_url. The call in a view would be something like
        'request.build_absolute_uri(resource.get_deny_url())'
        """
        return "/resource/%d/deny"%(self.pk,)

