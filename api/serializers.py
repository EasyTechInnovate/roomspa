from rest_framework import serializers
from .models import Pictures

class PicturesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pictures
        fields = ['profile_picture', 'more_pictures', 'certificate', 'national_id']
        read_only_fields = ['id', 'user']
    
    def validate_more_pictures(self, more_pictures):
        if len(more_pictures) > 6:
            raise serializers.ValidationError("Maximum of 6 additional pictures allowed")
        return more_pictures