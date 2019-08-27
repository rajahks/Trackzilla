from django.db import models
from apps.Users.models import AssetUser


class Resource(models.Model):
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
                                     related_name='res_being_used')  # TODO: Change this to our User model.

    # FK to the User who is currently managing the device.
    # This user would have admin privileges over the device.
    # TODO: Yet to be decided what these admin privileges are (This would mostly allow the user to edit fields)
    # Like the 'current user' above we do not allow the Device Admin User object
    # to be deleted when he has Resources assigned to him.
    # Enforce the constraint.
    device_admin = models.ForeignKey(AssetUser, on_delete=models.PROTECT,
                                     related_name='res_being_managed')  # TODO: change this to our user model.
    # TODO: Also check if we really need the 'related_name' fields for both the above 2 models.
    # The related_name allows us to fetch the resource list from the User model itself. Very useful as we would mostly
    # need to fetch these details per user. Might be better to let the ORM take care of this for us.

    # A resource could have the following states:
    # 'Unassigned' - When the resource is not assigned to any User
    # 'Assigned' - When the resource is assigned to a User and the user has not get Ackd it
    # 'Acknowledged' - When the assigned user acks that the resource is available with him.
    # Resources which are 'Unassigned' and which are 'Assigned' but not 'Acknowledged' have
    # to be notified to the device admin.

    RES_UNASSIGNED = 'R_UASS'
    RES_ASSIGNED = 'R_ASS'
    RES_ACKNOWLEDGED = 'R_ACK'

    RES_STATUS_CHOICES = [
        (RES_UNASSIGNED, 'Unassigned'),
        (RES_ASSIGNED, 'Assigned'),
        (RES_ACKNOWLEDGED, 'Acknowledged')
    ]

    # TODO: Check if the states defined above are ok.
    status = models.CharField(choices=RES_STATUS_CHOICES, default=RES_UNASSIGNED, max_length=20)

    # Any additional information about the device to go into this field.
    description = models.TextField()

    # TODO: Add a FK to a organisation.
    # Every resource will belong to an Organisation. This way we can have
    # resources belonging to different orgs on the same DB and filter them
    # based on a logged in user's organisation.
    # organisation = models.ForeignKey("app.Model", verbose_name=_(""), on_delete=models.CASCADE)

    class Meta:
        verbose_name = "resource"
        verbose_name_plural = "resources"

    def __str__(self):
        return self.name

    # def get_absolute_url(self):
    #     return reverse("_detail", kwargs={"pk": self.pk})
