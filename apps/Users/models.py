from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.urls import reverse

class UserManager(BaseUserManager):

  def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):
    if not email:
        raise ValueError('Users must have an email address')
    now = timezone.now()
    email = self.normalize_email(email)
    user = self.model(
        email=email,
        is_staff=is_staff, 
        is_active=True,
        is_superuser=is_superuser, 
        last_login=now,
        date_joined=now, 
        **extra_fields
    )
    user.set_password(password)
    user.save(using=self._db)
    return user

  def create_user(self, email, password, **extra_fields):
    return self._create_user(email, password, False, False, **extra_fields)

  def create_superuser(self, email, password, **extra_fields):
    user=self._create_user(email, password, True, True, **extra_fields)
    return user


class AssetUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=254, unique=True)
    name = models.CharField(max_length=254, null=False, blank=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    # The Org this user is part of. Do not allow deleting the parent Org if there are
    # TODO: Should we allow the user to be part of more than one Org?
    org = models.ForeignKey('Organization.Org', on_delete=models.PROTECT, null=True,
            blank=True, related_name='user_set')

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def get_absolute_url(self):
        return reverse("user-detail", kwargs={"pk": self.pk})

    def get_name(self):
      """Returns the string representing the name field

      Returns:
          str -- Should always be able to return a valid string because the field 'name'
                 is compulsory while signing up.
      """
      return self.name

    def get_email(self):
      return self.email

    def __str__(self):
      return self.name

#     def send_summary_email(self):
#         """Function when called sends a summary report to the user by email.
#         The summary email will contain the following data:
#             1) Resources needing action ( To be ack'd or denied ) with Ack & Deny links.
#             2) Resources in dispute with Resource detail page link.
#             3) Resources in use - With reassign button which would lead to the Resource update page.
#             4) Resources in Team - TODO: TBD what to include. Send full list or a link to 
#                 team page and tab which will show all the resources the team owns. 
#             5) Home page Button - Button with link to home page for performing other actions.

#         """
#         pass
