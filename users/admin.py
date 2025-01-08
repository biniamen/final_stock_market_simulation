from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = (
        'username', 
        'email', 
        'role', 
        'kyc_verified', 
        'account_balance', 
        'profit_balance', 
        'company_id', 
        'otp_code', 
        'otp_verified', 
        'otp_sent_at', 
        'otp_attempts',
    )

    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': (
                'role', 
                'kyc_document', 
                'kyc_verified', 
                'account_balance', 
                'profit_balance', 
                'company_id',
            )
        }),
        ('OTP Fields', {
            'fields': ('otp_code', 'otp_verified', 'otp_sent_at', 'otp_attempts'),
        }),
    )

    # Optionally, add filters or search fields related to company_id
    list_filter = UserAdmin.list_filter + ('role', 'company_id',)
    search_fields = UserAdmin.search_fields + ('company_id',)