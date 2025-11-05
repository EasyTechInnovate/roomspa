from rest_framework import serializers
from .models import TherapistAddress, Services, BankDetails, TherapistStatus

class TherapistAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapistAddress
        fields = ['address', 'service_radius', 'latitude', 'longitude']

class ServicesSerializer(serializers.ModelSerializer):
    services = serializers.DictField(
        child=serializers.IntegerField(min_value=0),
        allow_empty=True
    )

    class Meta:
        model = Services
        fields = ['services']

    def validate_services(self, value):
        valid_keys = {choice[0] for choice in Services.SERVICE_CHOICES}
        invalid = set(value.keys()) - valid_keys
        if invalid:
            raise serializers.ValidationError(
                f"Invalid service keys: {', '.join(invalid)}. "
                f"Allowed keys are: {', '.join(valid_keys)}."
            )
        return value

class BankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetails
        fields = ['id', 'bank_name', 'account_number', 'swift_code']

class TherapistStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapistStatus
        fields = ['status']