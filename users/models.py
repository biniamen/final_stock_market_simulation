from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# We'll do an inline import inside the method to avoid circular imports
# from stocks.models import ListedCompany

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
    company_id = models.IntegerField(null=True, blank=True)  # Will be used to reference ListedCompany’s primary key
    account_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, null=True, blank=True)
    profit_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, null=True, blank=True)
    date_registered = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    # OTP Fields
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_sent_at = models.DateTimeField(null=True, blank=True)
    otp_verified = models.BooleanField(default=False)
    otp_attempts = models.IntegerField(default=0)  # Track OTP retry attempts
    
    # Token Version
    token_version = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        """
        Custom save to handle:
        - Setting default balance for traders
        - Sending OTP email for new traders or company admins
        """
        is_new_user = not self.pk  # Check if the user is being created (no primary key yet)

        if is_new_user:
            # Set account_balance to 10000 if the role is 'trader'
            if self.role == 'trader':
                self.account_balance = 20000.00

            super().save(*args, **kwargs)  # Save once to generate a primary key (self.pk)

            # For 'trader' or 'company_admin', send OTP
            if self.role in ['trader', 'company_admin']:
                otp = generate_otp()
                self.otp_code = otp
                self.otp_sent_at = timezone.now()

                # Try to get the company name if role == 'company_admin'
                company_name = None
                if self.role == 'company_admin' and self.company_id:
                    try:
                        from stocks.models import ListedCompany  # Inline import to avoid circular dependency
                        company = ListedCompany.objects.get(id=self.company_id)
                        company_name = company.company_name
                    except ListedCompany.DoesNotExist:
                        company_name = None

                # Send verification email with role, and if 'company_admin' also pass company_name
                email_sent = send_verification_email(
                    to_email=self.email,
                    username=self.username,
                    otp=otp,
                    role=self.role,
                    company_name=company_name
                )

                if email_sent:
                    print(f"OTP sent to {self.email}")
                else:
                    print("Failed to send OTP.")

                super().save(update_fields=['otp_code', 'otp_sent_at'])
        else:
            # Existing user updates
            super().save(*args, **kwargs)

    def verify_otp(self, input_otp):
        """
        Verify the OTP provided by the user.
        """
        if self.otp_verified:
            return False, "OTP already verified."

        # Check OTP correctness and expiration
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
