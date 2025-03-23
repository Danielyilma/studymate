''' Definition module for different user management serializers'''
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class UserSerializer(serializers.ModelSerializer):
    ''' User serializer'''
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'provider']
        # required = ['password']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    '''serializer for authentication the user'''
    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
            if user.provider != 'local':
                raise serializers.ValidationError(f"Please use the {user.provider} provider to log in.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
        data = super().validate(attrs)
        return data