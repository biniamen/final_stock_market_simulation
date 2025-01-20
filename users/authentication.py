# users/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from .models import CustomUser

class CustomJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        try:
            token = super().get_validated_token(raw_token)
        except InvalidToken as e:
            raise AuthenticationFailed('Invalid token') from e

        user_id = token['user_id']
        token_version = token.get('token_version')

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise AuthenticationFailed('User not found.')

        if token_version != user.token_version:
            raise AuthenticationFailed('Token has been invalidated.')

        return token
