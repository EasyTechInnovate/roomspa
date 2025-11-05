from django.db import models
from django.conf import settings

class TherapistAddress(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='therapist_address')
    address = models.TextField()
    service_radius = models.DecimalField(max_digits=5, decimal_places=2, help_text="Service radius in kilometers")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

class Services(models.Model):
    SERVICE_CHOICES = [
        ('foot', 'Foot Massage'),
        ('thai', 'Thai Massage'),
        ('oil', 'Oil Massage'),
        ('aroma', 'Aroma Therapy'),
        ('4_hands_oil', '4 Hands Oil Massage'),
        ('pedicure', 'Pedicure/Manicure'),
        ('nails', 'Nails'),
        ('hair', 'Hair Fan'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='therapist_services')
    services = models.JSONField(blank=True, default=dict)

class BankDetails(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='therapist_bank_details'
    )
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=255)
    swift_code = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.bank_name} ({self.account_number})"
    
class TherapistStatus(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('unavailable', 'Unavailable'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='therapist_status'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unavailable'
    )

    def __str__(self):
        return f"{self.user.username} - {self.status.capitalize()}"