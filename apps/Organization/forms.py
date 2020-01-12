from django import forms
from .models import Org, Team
from django.contrib.auth import get_user_model

# Get the current custom User Model.
User = get_user_model()
