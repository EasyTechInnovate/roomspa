from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator

class UserProfileManager(BaseUserManager):
    def create_user(self, name, email=None, phone_number=None, password=None, **extra_fields):
        if not email and not phone_number:
            raise ValueError('Either Email or Phone Number must be provided')
        
        if email:
            email = self.normalize_email(email)
            
        user = self.model(
            name=name, 
            email=email, 
            phone_number=phone_number, 
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, name, email=None, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('verification_status', True)
        extra_fields.setdefault('role', 'admin')

        return self.create_user(name, email, phone_number, password, **extra_fields)

class UserProfile(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('therapist', 'Therapist'),
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    ]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    country_code = models.CharField(max_length=5, null=True, blank=True)
    number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\d{5,15}$')],
        null=True,
        blank=True
    )
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='prefer_not_to_say')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    consent = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    verification_status = models.BooleanField(default=False)
    date_created = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    objects = UserProfileManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    groups = models.ManyToManyField('auth.Group', related_name='userprofile_groups', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='userprofile_permissions', blank=True)

    def __str__(self):
        return self.name

    def is_verified(self):
        return self.verification_status

    def save(self, *args, **kwargs):
        if not self.email and not self.number:
            raise ValueError("Either email or phone number must be provided")
        if self.country_code and self.number:
            self.phone_number = f"{self.country_code}{self.number}"
        super().save(*args, **kwargs)