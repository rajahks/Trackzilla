from django.contrib.auth.models import User
from django.db import models


class AssetUser(User):

    # The Org this user is part of. If the parent org is deleted, so are the users under it.
    org_id = models.ForeignKey('Organization.Org', on_delete=models.CASCADE, null=True, blank=True)
