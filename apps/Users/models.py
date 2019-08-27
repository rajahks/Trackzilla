from django.contrib.auth.models import User
from django.db import models


class AssetUser(User):

    # The Org this user is part of. Do not allow deleting the parent Org if there are
    org_id = models.ForeignKey('Organization.Org', on_delete=models.PROTECT, null=True, blank=True)
