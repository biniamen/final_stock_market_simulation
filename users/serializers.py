from urllib import request
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.conf import settings

from users.utils import verify_captcha

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'role',
            'kyc_document',
            'kyc_verified',
            'account_balance',
            'profit_balance',
            'company_id',
            'date_registered',
            'last_login',
            'otp_verified',  
            'otp_attempts',
            'is_approved',
            'token_version',  # Include token_version


        )
        extra_kwargs = {
            'password': {'write_only': True},
            'kyc_verified': {'read_only': True},
            'is_approved': {'read_only': True},  # Make it read-only
            'account_balance': {'read_only': True},
            'profit_balance': {'read_only': True},
        }
    def validate(self, attrs):
        role = attrs.get('role')
        company_id = attrs.get('company_id')

        if role == 'company_admin' and not company_id:
            raise serializers.ValidationError({
                'company_id': 'This field is required for Company Admin role.'
            })
        if role != 'company_admin' and company_id:
            raise serializers.ValidationError({
                'company_id': 'This field should be null unless the role is Company Admin.'
            })
        return attrs

    def validate_username(self, value):
        """
        Ensure the username is unique.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists. Please choose a different username.")
        return value

    def validate_email(self, value):
        """
        Ensure the email is unique.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists. Please use a different email.")
        return value

    def create(self, validated_data):
        """
        Create a new user instance with hashed password.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            role=validated_data['role'],
            company_id=validated_data.get('company_id', None),  # Save company ID
            kyc_document=validated_data.get('kyc_document', None),
        )
        return user

    # def to_representation(self, instance):
    #     """
    #     Customize the serialized output.
    #     """
    #     representation = super().to_representation(instance)
    #     if instance.role != 'trader':
    #         representation.pop('account_balance', None)
    #         representation.pop('profit_balance', None)
    #     if instance.role != 'company_admin':
    #         representation.pop('company_id', None)
    #     return representation
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')  # Correctly get the request

        if instance.kyc_document:
            if request:
                representation['kyc_document'] = request.build_absolute_uri(instance.kyc_document.url)
            else:
                representation['kyc_document'] = instance.kyc_document.url
        else:
            representation['kyc_document'] = None

        return representation


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value
 
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for obtaining token pairs.
    Includes additional user data in the response.
    """

    # Include additional fields
    account_balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    profit_balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    role = serializers.CharField(read_only=True)
    kyc_verified = serializers.BooleanField(read_only=True)
    company_id = serializers.IntegerField(allow_null=True, read_only=True)
    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    token_version = serializers.IntegerField(read_only=True)  # Include token_version

    def validate(self, attrs):
        # Extract reCAPTCHA token
        captcha_token = self.initial_data.get('g-recaptcha-response')

        # if not captcha_token:
        #     raise serializers.ValidationError({"detail": "reCAPTCHA token is missing."})

        # # Verify reCAPTCHA
        # if not verify_captcha(captcha_token):
        #     raise serializers.ValidationError({"detail": "Invalid reCAPTCHA. Please try again."})

        data = super().validate(attrs)

        # Add additional responses here
        data.update({
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'kyc_verified': self.user.kyc_verified,
            'id': self.user.id,
            'company_id': self.user.company_id,
            'account_balance': self.user.account_balance,
            'profit_balance': self.user.profit_balance,
            'token_version': self.user.token_version,  # Include token_version

        })

        return data
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)