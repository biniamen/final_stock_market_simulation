from datetime import datetime, timedelta
import logging
from django.utils import timezone
import jwt
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password

from ethio_stock_simulation.utils import (
    generate_otp,
    send_verification_email,
    send_kyc_approved_email,
    send_kyc_rejected_email,
    send_account_kyc_verified_email,
)
from users.models import CustomUser
from users.throttles import LoginThrottle  # Suppose you have a custom throttle class
from users.utils import verify_captcha  # Suppose you have a reCAPTCHA verification utility
from .serializers import (
    UserSerializer,
    CustomTokenObtainPairSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterUser(generics.CreateAPIView):
    """
    API endpoint to register a new user.
    Includes reCAPTCHA validation if desired.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        # 1. Validate reCAPTCHA
        captcha_response = request.data.get('g-recaptcha-response')
        if not captcha_response or not verify_captcha(captcha_response):
            return Response(
                {"detail": "Invalid or missing reCAPTCHA. Please try again."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Check for uniqueness of username and email
        username = request.data.get('username')
        email = request.data.get('email')

        if User.objects.filter(username=username).exists():
            return Response(
                {"detail": "Username already exists. Please choose a different username."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "Email already exists. Please use a different email."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Serializer validation
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # NOTE: 
        # The `user.save()` method already handles sending the OTP email 
        # (in the CustomUser model’s save method). 
        # If you want to do an additional/explicit call here, you can,
        # but it's already handled by the model logic.

        return Response(
            {
                "detail": "Registration successful. Please check your email for the OTP.",
                "redirect_url": f"/verify-otp/?email={user.email}"
            },
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login endpoint using SimpleJWT.
    Blocks login if the user's KYC is not verified or the user is not approved.
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginThrottle]  # Example: 3 attempts/min

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            # Check KYC
            if not serializer.user.kyc_verified:
                return Response(
                    {"detail": "KYC not verified. Please wait for approval."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not serializer.user.is_approved:
                return Response(
                    {"detail": "Your account is not approved yet."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Increment token_version to invalidate previous tokens
            user = serializer.user
            user.token_version += 1
            user.save()

            # Generate new tokens with updated token_version
            refresh = RefreshToken.for_user(user)
            refresh['token_version'] = user.token_version
            access_token = refresh.access_token
            access_token['token_version'] = user.token_version

            return Response({
                'refresh': str(refresh),
                'access_token': str(access_token),
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'kyc_verified': user.kyc_verified,
                'id': user.id,
                'company_id': user.company_id,
                'account_balance': user.account_balance,
                'profit_balance': user.profit_balance,
                'token_version': user.token_version,
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    """
    API endpoint to list all users (accessible by regulators only).
    """
    if request.user.role != 'regulator':
        return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

    users = CustomUser.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_kyc_status(request, user_id):
    """
    API endpoint to approve or reject user KYC.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    # Only a regulator can update KYC status
    if request.user.role != 'regulator':
        return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

    action = request.data.get('action')
    if action == 'approve':
        if not user.otp_verified:
            return Response(
                {"detail": "Cannot approve KYC. OTP not verified by the user."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.kyc_verified = True
        user.is_approved = True
        user.save()

        # Send KYC approval email
        # Option 1: direct call to the "send_kyc_approved_email"
        email_sent = send_kyc_approved_email(user.email, user.username)
        if email_sent:
            logger.info(f"KYC Approved email sent to {user.email}")
        else:
            logger.warning(f"Failed to send KYC Approved email to {user.email}")

    elif action == 'reject':
        user.kyc_verified = False
        user.is_approved = False
        user.save()

        # Send KYC rejection email
        email_sent = send_kyc_rejected_email(user.email, user.username)
        if email_sent:
            logger.info(f"KYC Rejected email sent to {user.email}")
        else:
            logger.warning(f"Failed to send KYC Rejected email to {user.email}")
    else:
        return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "message": f"KYC status updated to {user.kyc_verified} and approval status to {user.is_approved} for user {user.username}."
        },
        status=status.HTTP_200_OK,
    )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not user.check_password(old_password):
            return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)


class ListUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Example usage: Only regulators can see all users
        if request.user.role != 'regulator':
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

        users = CustomUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class VerifyOTPView(APIView):
    """
    Verify OTP for user registration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp_code')

        if not email or not otp_code:
            return Response({"detail": "Email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            # If already verified
            if user.otp_verified:
                return Response({"detail": "OTP already verified."}, status=status.HTTP_200_OK)

            # Check if maximum attempts reached
            if user.otp_attempts >= 5:
                return Response(
                    {
                        "detail": "Maximum OTP attempts exceeded. Request a new OTP.",
                        "resend_required": True
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # Perform verification
            success, message = user.verify_otp(otp_code)
            if success:
                return Response({"detail": message, "verified": True}, status=status.HTTP_200_OK)
            else:
                # message can be either "Invalid or expired OTP." or "Maximum OTP attempts exceeded..."
                return Response({"detail": message, "resend_required": (user.otp_attempts >= 5)}, 
                                status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)


class ResendOTPView(APIView):
    """
    Resend OTP to the user's email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            # Add a cooldown period: e.g., 2 minutes
            if user.otp_sent_at and timezone.now() - user.otp_sent_at < timedelta(minutes=2):
                return Response({"detail": "Please wait before requesting a new OTP."},
                                status=status.HTTP_429_TOO_MANY_REQUESTS)

            # Generate and send a new OTP
            otp = generate_otp()
            user.otp_code = otp
            user.otp_sent_at = timezone.now()
            user.otp_attempts = 0  # Reset attempts
            user.save()

            # If user is company_admin, fetch the company name
            company_name = None
            if user.role == 'company_admin' and user.company_id:
                try:
                    from stocks.models import ListedCompany
                    company = ListedCompany.objects.get(id=user.company_id)
                    company_name = company.company_name
                except ListedCompany.DoesNotExist:
                    company_name = None

            send_verification_email(user.email, user.username, otp, role=user.role, company_name=company_name)
            return Response({"detail": "A new OTP has been sent to your email."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deactivate_user(request, user_id):
    """
    API endpoint to deactivate a user (set is_approved to False).
    Only accessible by regulators.
    """
    if request.user.role != 'regulator':
        return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    if not user.is_approved:
        return Response({"detail": "User is already deactivated."}, status=status.HTTP_400_BAD_REQUEST)

    user.is_approved = False
    user.save()

    # Send email notification about deactivation (optional)
    email_subject = "Account Deactivated"
    email_message = f"""
    Dear {user.username},

    Your account has been deactivated by an administrator. 
    You will no longer be able to log in to the system.

    If you believe this is a mistake, please contact support.
    """
    email = EmailMessage(
        subject=email_subject,
        body=email_message,
        from_email='noreply@yourapp.com',  # Replace with your actual sender email
        to=[user.email],
    )
    email.send()

    return Response(
        {"message": f"User {user.username} has been deactivated."},
        status=status.HTTP_200_OK,
    )


class ForgotPasswordView(APIView):
    """
    Handles password reset requests by generating a JWT token 
    and sending a reset link via email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Security measure: do not reveal if the email exists
            return Response({"detail": "If that email is registered, a reset link will be sent."},
                            status=status.HTTP_200_OK)

        # Generate JWT
        payload = {
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(minutes=30),  # 30 minutes validity
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # Build the reset URL
        reset_url = f"http://localhost:4200/reset-password?token={token}"

        subject = "Password Reset Request"
        body = f"""
Hello {user.username},

Please click the link below to reset your password:
{reset_url}

If you did not request this, you can ignore this email.
This link will expire in 30 minutes.

Best Regards,
Ethiopian Stock Market Simulation Team
"""
        email_message = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        try:
            email_message.send()
            logger.info(f"Password reset email sent to {user.email}.")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {e}")
            return Response({"detail": "Failed to send reset link. Please try again later."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {"detail": "If that email is registered, a reset link has been sent."},
            status=status.HTTP_200_OK
        )


class ResetPasswordView(APIView):
    """
    1. User clicks the link and provides new password with the token.
    2. We validate the token and set the user’s password.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not token or not new_password:
            return Response({"detail": "Token and new_password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Decode token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            # If token is expired or invalid, PyJWT raises an exception
        except jwt.ExpiredSignatureError:
            return Response({"detail": "Reset link has expired."}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.InvalidTokenError:
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate password
        try:
            validate_password(new_password)
        except ValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        # Update user’s password
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.password = make_password(new_password)
        user.save()

        return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)
