from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from ethio_stock_simulation.utils import generate_otp, send_verification_email


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('trader', 'Trader'),
        ('regulator', 'Regulator'),
        ('company_admin', 'Company Admin'),
    ]
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='trader')
    is_approved = models.BooleanField(default=False)
    kyc_document = models.FileField(upload_to='kyc_documents/', blank=True, null=True)
    kyc_verified = models.BooleanField(default=False)
    company_id = models.IntegerField(null=True, blank=True)
    account_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, null=True, blank=True)
    profit_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, null=True, blank=True)
    date_registered = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    # OTP Fields
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_sent_at = models.DateTimeField(null=True, blank=True)
    otp_verified = models.BooleanField(default=False)
    otp_attempts = models.IntegerField(default=0)  # Track OTP retry attempts

    def save(self, *args, **kwargs):
        is_new_user = not self.pk  # Check if the user is being created for the first time

        if is_new_user:
            # Set account_balance to 10000 if the role is 'trader'
            if self.role == 'trader':
                self.account_balance = 10000.00

            super().save(*args, **kwargs)  # Save the user to generate a primary key

            if self.role in ['trader', 'company_admin']:
                otp = generate_otp()
                self.otp_code = otp
                self.otp_sent_at = timezone.now()
                email_sent = send_verification_email(self.email, self.username, otp)
                if email_sent:
                    print(f"OTP sent to {self.email}")
                else:
                    print("Failed to send OTP.")
                super().save(update_fields=['otp_code', 'otp_sent_at'])  # Save OTP-related fields
        else:
            super().save(*args, **kwargs)

    def verify_otp(self, input_otp):
        """
        Verify the OTP provided by the user.
        """
        if self.otp_verified:
            return False, "OTP already verified."

        if self.otp_code == input_otp and self.otp_sent_at + timedelta(minutes=10) > timezone.now():
            self.otp_verified = True
            self.otp_code = None  # Clear the OTP after successful verification
            self.otp_attempts = 0  # Reset attempts
            self.save()
            return True, "OTP verified successfully."
        else:
            self.otp_attempts += 1
            self.save()
            if self.otp_attempts >= 5:
                return False, "Maximum OTP attempts exceeded. Request a new OTP."
            return False, "Invalid or expired OTP."

    # Methods for Trader financial updates
    def update_account_balance(self, amount):
        if self.role == 'trader' and self.account_balance is not None:
            self.account_balance += amount
            self.save()

    def update_profit_balance(self, amount):
        if self.role == 'trader' and self.profit_balance is not None:
            self.profit_balance += amount
            self.save()

    # KYC Approval and Rejection for Regulator role
    def approve_kyc(self):
        if self.kyc_document:
            self.kyc_verified = True
            self.save()
            

    def reject_kyc(self):
        self.kyc_verified = False
        self.save()

    # Company Admin-specific methods
    def link_company(self, company_id):
        if self.role == 'company_admin':
            self.company_id = company_id
            self.save()

    def unlink_company(self):
        if self.role == 'company_admin':
            self.company_id = None
            self.save()
