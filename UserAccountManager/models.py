'''defining User model'''
from django.db import models
from uuid import uuid4
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import validate_email
from django.contrib.auth.validators import UnicodeUsernameValidator
from base_model import TimeStampMixin
from UserAccountManager.managers import UserManager

class User(AbstractBaseUser, PermissionsMixin, TimeStampMixin):
    '''custom user class'''

    validate_username = UnicodeUsernameValidator()

    uuid = models.UUIDField(unique=True, default=uuid4, editable=False)
    email = models.EmailField(
        max_length=255,
        unique=True,
        validators=[validate_username, validate_email],
    )
    first_name = models.CharField(max_length=60, blank=True)
    last_name = models.CharField(max_length=128, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    provider = models.CharField(max_length=60, default='local')

    USERNAME_FIELD = EMAIL_FIELD = 'email'

    objects = UserManager()

    def __str__(self) -> str:
        return self.email