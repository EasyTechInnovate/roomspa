from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import UserProfile
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['name', 'email', 'gender', 'consent']

class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'name', 'email']