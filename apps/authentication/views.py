"""
Authentication API Views for User Registration and Login.
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.authentication.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserDetailSerializer
)

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """
    API endpoint for registering a new user.
    Accessible publicly without authentication.
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    @extend_schema(
        tags=['Authentication'],
        summary='Register a new user',
        description='Creates a new user account with name, unique email, and secure password.',
        request=UserRegistrationSerializer,
        responses={
            201: OpenApiResponse(
                response=UserDetailSerializer,
                description='User successfully registered.'
            ),
            400: OpenApiResponse(description='Validation error.')
        }
    )
    def post(self, request, *args, **kwargs):
        logger.info("Processing user registration request for email: %s", request.data.get('email'))
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        logger.info("User registered successfully [User ID: %s, Email: %s]", user.id, user.email)
        return Response(
            {
                'success': True,
                'message': 'User registered successfully.',
                'data': UserDetailSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """
    API endpoint for logging in an existing user.
    Returns JWT access and refresh tokens.
    """
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    @extend_schema(
        tags=['Authentication'],
        summary='Log in user & get JWT token',
        description='Authenticates user credentials (email & password) and returns JWT access & refresh tokens.',
        request=UserLoginSerializer,
        responses={
            200: OpenApiResponse(
                response=UserLoginSerializer,
                description='Authentication successful.'
            ),
            400: OpenApiResponse(description='Invalid credentials or validation error.')
        }
    )
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        logger.info("Processing login attempt for email: %s", email)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_info = serializer.get_user(None)
        tokens = serializer.get_tokens(None)

        logger.info("User authenticated successfully [User ID: %s, Email: %s]", user_info['id'], user_info['email'])
        return Response(
            {
                'success': True,
                'message': 'Login successful.',
                'user': user_info,
                'tokens': tokens
            },
            status=status.HTTP_200_OK
        )
