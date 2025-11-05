from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

class Pictures(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='therapist_pictures')
    profile_picture = models.URLField()
    more_pictures = ArrayField(models.URLField(), blank=True, default=list)
    certificate = models.URLField(blank=True, null=True)
    national_id = models.URLField(blank=True, null=True)