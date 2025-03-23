'''Defining UserManager class'''
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    '''
    UserManager that implements
        create : create the user any user
        user create : handles necessary check for normal user creation
        super user create : checks for superuser creation
    '''

    def create(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')

        email = self.normalize_email(email=email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()

        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_susperuser', False)

        if extra_fields.get('is_superuser') is True:
            raise ValueError('user must have is_superuser False')

        return self.create(email, password, **extra_fields)
    
    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_superuser') is False:
            raise ValueError('superuser must have is_superuser True')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('superuser must have is_staff True')
        
        return self.create(email, password, **extra_fields)