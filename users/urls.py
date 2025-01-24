from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import ForgotPasswordView, ListUsersView, RegisterUser, CustomTokenObtainPairView, ResendOTPView, ResetPasswordView, VerifyOTPView, deactivate_user, list_users, update_kyc_status
from django.urls import path, include
from .views import ChangePasswordView

urlpatterns = [
    path('register/', RegisterUser.as_view(), name='register'),  # Registration endpoint
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # Custom login endpoint
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh JWT tokens
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    # New endpoints for Regulators:
    path('users/', list_users, name='list_users'),  # Endpoint to list all registered users (Regulators only)
    #path('users/<int:user_id>/kyc/', update_kyc_status, name='update_kyc_status'),  # Endpoint to approve/reject KYC
    path('<int:user_id>/kyc/', update_kyc_status, name='update_kyc_status'),  # Endpoint to approve/reject KYC
    path('api/stocks/', include('stocks.urls')),
    path('list/', ListUsersView.as_view(), name='list-users'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('<int:user_id>/deactivate/', deactivate_user, name='deactivate_user'),  # Added deactivation URL
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),


]
