from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class AssetUser(User):

    # The Org this user is part of. Do not allow deleting the parent Org if there are
    org_id = models.ForeignKey('Organization.Org', on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse("user-detail", kwargs={"pk": self.pk})

    def send_summary_email(self):
        """Function when called sends a summary report to the user by email.
        The summary email will contain the following data:
            1) Resources needing action ( To be ack'd or denied ) with Ack & Deny links.
            2) Resources in dispute with Resource detail page link.
            3) Resources in use - With reassign button which would lead to the Resource update page.
            4) Resources in Team - TODO: TBD what to include. Send full list or a link to 
                team page and tab which will show all the resources the team owns. 
            5) Home page Button - Button with link to home page for performing other actions.

        """
        pass
    