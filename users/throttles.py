# users/throttles.py

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class LoginRateThrottle(UserRateThrottle):
    scope = 'login'

class OTPVerifyRateThrottle(UserRateThrottle):
    scope = 'otp_verify'

class OTPResendRateThrottle(UserRateThrottle):
    scope = 'otp_resend'


class LoginThrottle(AnonRateThrottle):
    scope = 'login'
