from django.db import models
from apps.Users.models import AssetUser
from apps.Organization.models import Org
from django.urls import reverse

import json
from django.forms.models import model_to_dict
from django.utils import timezone


from .middleware import _get_django_request

import logging
logger = logging.getLogger(__name__)

class HistoryField(models.TextField):
    description = "Essentially a Textfield which stores the JSON representation of the history list."

    def __init__(self, *args, **kwargs):
        super(HistoryField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            value = []

        if isinstance(value, list):
            return value

        return json.loads(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return json.loads(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        return json.dumps(value)


class ChangeHistoryMixin(models.Model):
    """
    A model mixin that tracks model fields' values and records the changes made to it in
    JSON format. A new field 'history' is added to the object.
    """

    # Mark as abstract so that a separate table is not created and the history field is
    # included into the existing table.
    class Meta:
        abstract = True

    # History is stored in the below model in JSON format. HistoryField is essentially a
    # Textfield with operations to serialize and de-serialize data.
    # TODO: Make the field name configurable like we are allowed in case of template_name in CBV
    # TODO: Should I include Zlib compression like in PickleField() as the history can get quite long ?
    history = HistoryField(editable=True,default=[])

    # Function, if defined, is called after the model is converted to dict using model_to_dict
    # function. This is required as at time we would want to handle certain fields in a
    # certain way Eg: Storing 'username' or email instead of ID value for ForeignKeys.
    # Example customer Serializer
    # def CustomFieldSerializer(instance, object_dict, *args, **kwargs):
    #   for field in object_dict:
    #     field_val = getattr(instance,field)
    #     if issubclass(field_val.__class__, User):
    #         object_dict[field] = field_val.get_username()

    #     # Add other field which need customer processing.
    #   return
    history_process_change_dict = None

    # Set the number of history entries we wish to store.
    # By default there is no limit and entries will be prepended. If a value is set, then
    # while inserting the record the list if we have greater number of entries, the oldest
    # records are removed.
    history_max_entry_count = None

    # In addition to tracking what changed, it is sometimes important to track who changed it as well.
    # This maynot be required to all users or there could be different ways to do this.
    # Making this configurable by allowing the user to specify a function which would return
    # a string which will be stored in the 'who' field.
    # The below field should be set to a function which when called returns a string
    # which will be stored in the 'who' field. Function is not called when it is None.
    history_get_user = None

    def __init__(self, *args, **kwargs):
        super(ChangeHistoryMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        # diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        diffs = [ { 'field':k, 'prev':v, 'cur': d2[k] } for k, v in d1.items() if v != d2[k]]
        #return dict(diffs)
        return diffs

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    @property
    def _dict(self):
        object_dict =  model_to_dict(self, fields=[field.name for field in
                             self._meta.fields])
        # Call the function which allows to perform custom processing on this dict.
        # call it only if the user has declared a customer serializer.
        if self.history_process_change_dict is not None:
            self.history_process_change_dict(object_dict=object_dict) # self passed automatically by python.
        return object_dict

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        changesDict = self.diff

        # Let's construct the history record entry and add it to the dict.
        # Each record is further going to be dictionary stored in the DB as a string.

        # We need to keep track of which user updated the data. Check if the user has
        # assigned a callable to fetch it. Else we will initialize it to be empty.
        who = None
        if self.history_get_user is not None:
            if callable(self.history_get_user):
                who = self.history_get_user()
            else:
                logger.error("history_get_user initialized with a non-callable")

        # only add the 'who' field if we have a string value.
        if who is not None and isinstance(who,str):
            entry = {
                'who'  : str(who),
                'when' : timezone.now().isoformat(),
                'what' : changesDict,
            }
        else:
            entry = {
                'when' : timezone.now().isoformat(),
                'what' : changesDict,
            }

        # prepend this entry into the list
        if isinstance(self.history, list):
            self.history.insert(0,entry)
            if isinstance(self.history_max_entry_count, int):
                if self.history_max_entry_count >= 0:
                # Value has been specified. Trim the list. Value of 0 deletes the whole list.
                    del self.history[self.history_max_entry_count: ]
            logger.debug('Added the following record to history:\n %s'%(str(entry),))
        else:
            logger.error("History field not saved initially as list!!")

        # Let's not hold up the save. Save and reset the initial state.
        super(ChangeHistoryMixin, self).save(*args, **kwargs)
        self.__initial = self._dict


def CustomFieldSerializer(instance, object_dict, *args, **kwargs):
    for field in object_dict:
            # for FileFields
            field_val = getattr(instance,field)
            if issubclass(field_val.__class__, AssetUser):
                object_dict[field] = field_val.get_username()

            # TODO: add other non-serializable field types
    return

def history_get_user(*args,**kwargs):
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
        who = request_obj.user.email  # We wish to store the email id in the who field.
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
    current_user = models.ForeignKey(AssetUser, on_delete=models.PROTECT,
                                     related_name='res_being_used')

    # FK to the previous user of the device. The field is updated when the resource is
    # transferred from one person to another person. Current_user will be the one who to
    # whom the resource is assigned and the previous_user will be the one who previously
    # was using the resource.
    previous_user = models.ForeignKey( AssetUser, on_delete=models.SET_NULL, blank=True,
                                       null=True, related_name='res_prev_used')

    # FK to the User who is currently managing the device.
    # This user would have admin privileges over the device.
    # TODO: Yet to be decided what these admin privileges are (This would mostly allow the user to edit fields)
    # Like the 'current user' above we do not allow the Device Admin User object
    # to be deleted when he has Resources assigned to him.
    # Enforce the constraint.
    device_admin = models.ForeignKey(AssetUser, on_delete=models.PROTECT,
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
    org_id = models.ForeignKey(Org, on_delete=models.PROTECT, null=True)


    # Add a custom configuration for the ChangeHistoryMixin.
    history_process_change_dict = CustomFieldSerializer
    history_get_user = history_get_user
    history_max_entry_count = 5

    class Meta:
        verbose_name = "resource"
        verbose_name_plural = "resources"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("resource-detail", kwargs={"pk": self.pk})

    def get_update_url(self):
        return reverse("resource-update", kwargs={"pk": self.pk})

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

