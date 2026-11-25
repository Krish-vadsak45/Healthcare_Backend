"""
Serializers for User Registration, Login, and Profile representation.
"""
import logging
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema_field
from apps.authentication.models import User

logger = logging.getLogger(__name__)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for new user registration.
    Validates name, unique email, and strong password.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters long."
    )

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'password', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized_email

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'].strip(),
            password=validated_data['password']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login with email and password.
    Returns access and refresh JWT tokens alongside user metadata.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    tokens = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').strip().lower()
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError("Both email and password are required.")

        user = authenticate(username=email, password=password)

        if not user:
            logger.warning("Failed login attempt for email: %s", email)
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            logger.warning("Inactive user attempted login: %s", email)
            raise serializers.ValidationError("This user account has been disabled.")

        self.user_obj = user
        return attrs

    @extend_schema_field(serializers.DictField())
    def get_tokens(self, obj):
        refresh = RefreshToken.for_user(self.user_obj)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @extend_schema_field(serializers.DictField())
    def get_user(self, obj):
        return {
            'id': self.user_obj.id,
            'name': self.user_obj.name,
            'email': self.user_obj.email,
        }


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Read-only public serializer for user information.
    """
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'created_at')
        read_only_fields = fields
